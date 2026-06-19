import io
import json
import re
import stat
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.problem import Problem
from app.models.test_case import TestCase
from app.models.user import User
from app.repositories.problems import (
    allocate_problem_display_id,
    get_user_problem,
    replace_problem_tags,
)
from app.schemas.problem_import import ImportedTestCase, ProblemImportResult, ZipProblemMetadata
from app.services.problems import _ensure_slug_available, _generate_slug, _normalize_slug, _resolve_topics, _to_detail

ZIP_MAX_BYTES = 10 * 1024 * 1024
ZIP_MAX_FILES = 50
ZIP_MAX_UNCOMPRESSED_BYTES = 2 * 1024 * 1024
ZIP_MAX_SINGLE_FILE_BYTES = 512 * 1024
ZIP_MAX_COMPRESSION_RATIO = 20
TEST_CASE_MAX_COUNT = 100
TEST_CASE_MAX_INPUT_BYTES = 256 * 1024
TEST_CASE_MAX_OUTPUT_BYTES = 256 * 1024

ALLOWED_EXTENSIONS = {".json", ".md", ".in", ".out"}
ROOT_FILES = {
    "problem.json",
    "statement.md",
    "solution.md",
    "input_format.md",
    "output_format.md",
    "constraints.md",
}


@dataclass(frozen=True)
class ZipFileEntry:
    path: str
    content: bytes


def _zip_error(code: str, message: str, http_status: int = status.HTTP_400_BAD_REQUEST) -> HTTPException:
    return HTTPException(status_code=http_status, detail={"code": code, "message": message})


def _natural_key(value: str) -> list[int | str]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]


def _is_symlink(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0o170000
    return stat.S_ISLNK(mode)


def _validate_raw_path(name: str) -> list[str]:
    if "\\" in name or re.match(r"^[A-Za-z]:", name):
        raise _zip_error("ZIP_PATH_NOT_ALLOWED", "ZIP contains an unsafe path")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise _zip_error("ZIP_PATH_NOT_ALLOWED", "ZIP contains an unsafe path")
    parts = [part for part in path.parts if part not in ("", ".")]
    if not parts:
        raise _zip_error("ZIP_PATH_NOT_ALLOWED", "ZIP contains an empty path")
    return parts


def _strip_single_top_level(entries: list[tuple[zipfile.ZipInfo, list[str]]]) -> list[tuple[zipfile.ZipInfo, str]]:
    root_mode = False
    top_level: str | None = None
    normalized: list[tuple[zipfile.ZipInfo, str]] = []

    for info, parts in entries:
        first = parts[0]
        if first in ROOT_FILES or first == "tests":
            root_mode = True
            logical_parts = parts
        else:
            if len(parts) < 2:
                raise _zip_error("ZIP_PATH_NOT_ALLOWED", "ZIP file must contain problem files")
            if top_level is None:
                top_level = first
            elif top_level != first:
                raise _zip_error("ZIP_PATH_NOT_ALLOWED", "ZIP must use a single top-level directory")
            logical_parts = parts[1:]

        if root_mode and top_level is not None:
            raise _zip_error("ZIP_PATH_NOT_ALLOWED", "ZIP cannot mix root files and top-level directories")
        normalized.append((info, "/".join(logical_parts)))

    return normalized


def _validate_logical_path(path: str) -> None:
    parts = path.split("/")
    suffix = PurePosixPath(path).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise _zip_error("ZIP_FILE_TYPE_NOT_ALLOWED", "ZIP contains an unsupported file type")
    if len(parts) == 1 and path in ROOT_FILES:
        return
    if len(parts) == 2 and parts[0] == "tests" and suffix in {".in", ".out"} and parts[1].removesuffix(suffix):
        return
    raise _zip_error("ZIP_PATH_NOT_ALLOWED", "ZIP contains an unsupported path")


def _read_zip_entries(zip_bytes: bytes) -> dict[str, bytes]:
    if len(zip_bytes) > ZIP_MAX_BYTES:
        raise _zip_error("ZIP_FILE_TOO_LARGE", "ZIP file is too large", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    try:
        archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile as exc:
        raise _zip_error("ZIP_INVALID_ARCHIVE", "Uploaded file is not a valid ZIP archive") from exc

    with archive:
        file_infos = [info for info in archive.infolist() if not info.is_dir()]
        if not file_infos:
            raise _zip_error("ZIP_ARCHIVE_EMPTY", "ZIP archive is empty")
        if len(file_infos) > ZIP_MAX_FILES:
            raise _zip_error("ZIP_FILE_COUNT_EXCEEDED", "ZIP contains too many files")

        total_uncompressed = 0
        raw_entries: list[tuple[zipfile.ZipInfo, list[str]]] = []
        for info in file_infos:
            if info.flag_bits & 0x1:
                raise _zip_error("ZIP_PATH_NOT_ALLOWED", "Encrypted ZIP entries are not allowed")
            if _is_symlink(info):
                raise _zip_error("ZIP_PATH_NOT_ALLOWED", "Symbolic links are not allowed")
            if info.file_size > ZIP_MAX_SINGLE_FILE_BYTES:
                raise _zip_error("ZIP_FILE_TOO_LARGE", "A ZIP entry is too large")
            total_uncompressed += info.file_size
            if total_uncompressed > ZIP_MAX_UNCOMPRESSED_BYTES:
                raise _zip_error("ZIP_UNCOMPRESSED_SIZE_EXCEEDED", "ZIP uncompressed content is too large")
            if info.compress_size > 0 and info.file_size / info.compress_size > ZIP_MAX_COMPRESSION_RATIO:
                raise _zip_error("ZIP_COMPRESSION_RATIO_EXCEEDED", "ZIP compression ratio is too high")
            parts = _validate_raw_path(info.filename)
            if PurePosixPath(parts[-1]).suffix.lower() not in ALLOWED_EXTENSIONS:
                raise _zip_error("ZIP_FILE_TYPE_NOT_ALLOWED", "ZIP contains an unsupported file type")
            raw_entries.append((info, parts))

        logical_entries = _strip_single_top_level(raw_entries)
        entries: dict[str, bytes] = {}
        for info, path in logical_entries:
            _validate_logical_path(path)
            if path in entries:
                raise _zip_error("ZIP_DUPLICATE_PATH", "ZIP contains duplicate logical paths")
            entries[path] = archive.read(info)
        return entries


def _decode_text(
    entries: dict[str, bytes],
    path: str,
    *,
    required: bool = False,
    missing_error_code: str = "ZIP_STATEMENT_REQUIRED",
) -> str | None:
    data = entries.get(path)
    if data is None:
        if required:
            raise _zip_error(missing_error_code, f"{path} is required")
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _zip_error("ZIP_INVALID_ENCODING", "ZIP files must use UTF-8 encoding") from exc


def _load_metadata(entries: dict[str, bytes]) -> ZipProblemMetadata:
    raw = entries.get("problem.json")
    if raw is None:
        raise _zip_error("ZIP_PROBLEM_METADATA_INVALID", "problem.json is required")
    try:
        data = json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise _zip_error("ZIP_INVALID_ENCODING", "problem.json must use UTF-8 encoding") from exc
    except json.JSONDecodeError as exc:
        raise _zip_error("ZIP_INVALID_JSON", "problem.json is not valid JSON") from exc
    try:
        return ZipProblemMetadata.model_validate(data)
    except ValidationError as exc:
        raise _zip_error("ZIP_PROBLEM_METADATA_INVALID", "problem.json metadata is invalid") from exc


def _load_test_cases(entries: dict[str, bytes], metadata: ZipProblemMetadata) -> list[ImportedTestCase]:
    pairs: dict[str, dict[str, bytes]] = {}
    for path, content in entries.items():
        if not path.startswith("tests/"):
            continue
        name_with_suffix = path.removeprefix("tests/")
        suffix = PurePosixPath(name_with_suffix).suffix.lower()
        name = name_with_suffix[: -len(suffix)]
        pairs.setdefault(name, {})[suffix] = content

    if not pairs:
        raise _zip_error("ZIP_TEST_CASE_REQUIRED", "At least one test case pair is required")
    if len(pairs) > TEST_CASE_MAX_COUNT:
        raise _zip_error("ZIP_TEST_CASE_LIMIT_EXCEEDED", "ZIP contains too many test cases")

    missing_pairs = [name for name, value in pairs.items() if ".in" not in value or ".out" not in value]
    if missing_pairs:
        raise _zip_error("ZIP_TEST_CASE_PAIR_MISMATCH", "Each test case must include matching .in and .out files")

    sorted_names = sorted(pairs, key=_natural_key)
    sample_names = set(metadata.sample_case_names or [sorted_names[0]])
    if not sample_names.issubset(set(sorted_names)):
        raise _zip_error("ZIP_PROBLEM_METADATA_INVALID", "sample_case_names references missing test cases")

    test_cases: list[ImportedTestCase] = []
    for index, name in enumerate(sorted_names, start=1):
        input_bytes = pairs[name][".in"]
        output_bytes = pairs[name][".out"]
        if len(input_bytes) > TEST_CASE_MAX_INPUT_BYTES or len(output_bytes) > TEST_CASE_MAX_OUTPUT_BYTES:
            raise _zip_error("ZIP_FILE_TOO_LARGE", "A test case input or output file is too large")
        try:
            input_text = input_bytes.decode("utf-8")
            output_text = output_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise _zip_error("ZIP_INVALID_ENCODING", "Test case files must use UTF-8 encoding") from exc
        test_cases.append(
            ImportedTestCase(
                case_index=index,
                name=name,
                input_text=input_text,
                expected_output_text=output_text,
                is_sample=name in sample_names,
            )
        )
    return test_cases


def import_problem_zip(db: Session, *, user: User, zip_bytes: bytes) -> ProblemImportResult:
    entries = _read_zip_entries(zip_bytes)
    metadata = _load_metadata(entries)
    statement = (_decode_text(entries, "statement.md", required=True) or "").strip()
    if not statement:
        raise _zip_error("ZIP_STATEMENT_REQUIRED", "statement.md is required")
    test_cases = _load_test_cases(entries, metadata)

    if metadata.slug is None:
        slug = _generate_slug(db, user_id=user.id, title=metadata.title)
    else:
        slug = _normalize_slug(metadata.slug)
        if not slug:
            raise _zip_error("ZIP_PROBLEM_METADATA_INVALID", "slug is invalid", status.HTTP_422_UNPROCESSABLE_ENTITY)
        _ensure_slug_available(db, user_id=user.id, slug=slug)

    topics = _resolve_topics(db, metadata.topic_ids)
    first_sample = next((case for case in test_cases if case.is_sample), test_cases[0])

    problem = Problem(
        display_id=allocate_problem_display_id(db, user_id=user.id),
        title=metadata.title,
        slug=slug,
        source="zip_import",
        source_url=metadata.source_url,
        difficulty=metadata.difficulty,
        estimated_minutes=metadata.estimated_minutes,
        description_markdown=statement,
        input_format=_decode_text(entries, "input_format.md"),
        output_format=_decode_text(entries, "output_format.md"),
        constraints=_decode_text(entries, "constraints.md"),
        sample_input=first_sample.input_text,
        sample_output=first_sample.expected_output_text,
        hint=None,
        solution_markdown=_decode_text(entries, "solution.md"),
        solution_code_cpp=None,
        solution_code_python=None,
        is_ai_generated=False,
        is_published=False,
        created_by_user_id=user.id,
    )

    try:
        db.add(problem)
        db.flush()
        replace_problem_tags(db, problem=problem, topics=topics)
        for case in test_cases:
            db.add(
                TestCase(
                    problem_id=problem.id,
                    case_index=case.case_index,
                    name=case.name,
                    input_text=case.input_text,
                    expected_output_text=case.expected_output_text,
                    is_sample=case.is_sample,
                    is_hidden=False,
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        raise

    refreshed = get_user_problem(db, problem_id=problem.id, user_id=user.id) or problem
    return ProblemImportResult(problem=_to_detail(refreshed), test_cases_count=len(test_cases))
