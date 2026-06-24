import io
import stat
import zipfile
from uuid import uuid4

from sqlalchemy import select

from app.core.config import settings
from app.models.problem import Problem
from app.models.test_case import TestCase as ProblemTestCase
from app.models.topic import Topic


def _zip_bytes(files: dict[str, str | bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, content in files.items():
            archive.writestr(path, content)
    return buffer.getvalue()


def _valid_zip(**overrides: str | bytes) -> bytes:
    files: dict[str, str | bytes] = {
        "problem.json": (
            '{"title":"ZIP Prefix Sum","slug":"zip-prefix-sum","difficulty":"basic",'
            '"estimated_minutes":30}'
        ),
        "statement.md": "Given an array, answer range sum queries.",
        "input_format.md": "The first line contains n and q.",
        "output_format.md": "Print one answer per query.",
        "constraints.md": "1 <= n, q <= 100000",
        "solution.md": "Use prefix sums.",
        "tests/01.in": "5 1\n1 2 3 4 5\n1 3\n",
        "tests/01.out": "6\n",
        "tests/02.in": "3 1\n2 2 2\n1 3\n",
        "tests/02.out": "6\n",
    }
    files.update(overrides)
    return _zip_bytes(files)


def _post_zip(client, content: bytes, filename: str = "problem.zip"):
    return client.post(
        "/api/problems/import/zip",
        files={"file": (filename, content, "application/zip")},
    )


def _register(client, prefix: str = "zip-user") -> dict:
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/auth/register",
        json={
            "student_id": f"{prefix}_{suffix}",
            "password": "password123",
            "name": "导入用户",
            "current_level": "elementary",
            "goal_track": "self_study",
            "goal_description": None,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


def _create_problem(client, title: str = "Manual Problem") -> dict:
    response = client.post(
        "/api/problems",
        json={
            "title": title,
            "difficulty": "beginner",
            "description_markdown": "Manual problem statement.",
            "topic_ids": [],
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


def _error_code(response) -> str:
    return response.json()["error"]["code"]


def test_import_zip_success_creates_problem_and_test_cases(client, db_session) -> None:
    _register(client)

    response = _post_zip(client, _valid_zip())

    assert response.status_code == 201
    payload = response.json()["data"]
    problem = payload["problem"]
    assert payload["test_cases_count"] == 2
    assert problem["display_id"] == 1
    assert problem["source"] == "zip_import"
    assert problem["is_ai_generated"] is False
    assert problem["is_published"] is False
    assert problem["sample_input"] == "5 1\n1 2 3 4 5\n1 3\n"
    assert problem["sample_output"] == "6\n"

    cases = list(
        db_session.scalars(
            select(ProblemTestCase)
            .where(ProblemTestCase.problem_id == problem["id"])
            .order_by(ProblemTestCase.case_index)
        ).all()
    )
    assert [(case.case_index, case.name, case.is_sample) for case in cases] == [(1, "01", True), (2, "02", False)]
    assert cases[0].input_text == "5 1\n1 2 3 4 5\n1 3\n"
    assert cases[0].expected_output_text == "6\n"
    assert cases[0].is_hidden is False


def test_import_zip_uses_declared_sample_case_and_natural_sort(client, db_session) -> None:
    _register(client)
    content = _zip_bytes(
        {
            "problem.json": (
                '{"title":"Natural Sort","difficulty":"basic","sample_case_names":["10"]}'
            ),
            "statement.md": "Sort cases naturally.",
            "tests/2.in": "2\n",
            "tests/2.out": "2\n",
            "tests/10.in": "10\n",
            "tests/10.out": "10\n",
        }
    )

    response = _post_zip(client, content)

    assert response.status_code == 201
    problem = response.json()["data"]["problem"]
    cases = list(
        db_session.scalars(
            select(ProblemTestCase)
            .where(ProblemTestCase.problem_id == problem["id"])
            .order_by(ProblemTestCase.case_index)
        ).all()
    )
    assert [(case.case_index, case.name, case.is_sample) for case in cases] == [(1, "2", False), (2, "10", True)]
    assert problem["sample_input"] == "10\n"


def test_import_zip_display_id_shares_user_problem_sequence(client) -> None:
    _register(client)
    first = _create_problem(client, title="Manual Before ZIP")

    response = _post_zip(client, _valid_zip())

    assert response.status_code == 201
    imported = response.json()["data"]["problem"]
    assert first["display_id"] == 1
    assert imported["display_id"] == 2


def test_import_zip_belongs_to_current_user(client) -> None:
    first_user = _register(client, "zip-owner-a")
    first_response = _post_zip(client, _valid_zip())
    assert first_response.status_code == 201
    first_problem = first_response.json()["data"]["problem"]

    client.post("/api/auth/logout")
    second_user = _register(client, "zip-owner-b")
    second_response = _post_zip(
        client,
        _valid_zip(**{"problem.json": '{"title":"Second User ZIP","slug":"zip-prefix-sum","difficulty":"basic"}'}),
    )
    assert second_response.status_code == 201
    second_problem = second_response.json()["data"]["problem"]

    assert first_user["id"] != second_user["id"]
    assert first_problem["created_by_user_id"] == first_user["id"]
    assert second_problem["created_by_user_id"] == second_user["id"]
    assert first_problem["display_id"] == 1
    assert second_problem["display_id"] == 1


def test_import_zip_supports_single_top_level_directory(client) -> None:
    _register(client)
    content = _zip_bytes(
        {
            "pkg/problem.json": '{"title":"Nested Package","difficulty":"beginner"}',
            "pkg/statement.md": "Nested package statement.",
            "pkg/tests/01.in": "1\n",
            "pkg/tests/01.out": "1\n",
        }
    )

    response = _post_zip(client, content)

    assert response.status_code == 201
    assert response.json()["data"]["problem"]["title"] == "Nested Package"


def test_import_zip_can_associate_published_topic(client, published_topic) -> None:
    _register(client)
    content = _valid_zip(
        **{
            "problem.json": (
                '{"title":"Topic Linked ZIP","difficulty":"basic","topic_ids":["'
                + str(published_topic.id)
                + '"]}'
            )
        }
    )

    response = _post_zip(client, content)

    assert response.status_code == 201
    topic_tags = response.json()["data"]["problem"]["topic_tags"]
    assert [tag["id"] for tag in topic_tags] == [str(published_topic.id)]


def test_import_zip_rejects_unpublished_topic(client, db_session) -> None:
    _register(client)
    topic = Topic(
        title="Draft Topic",
        slug=f"draft-topic-{uuid4().hex}",
        category="Test",
        level="beginner",
        difficulty_score=2,
        summary="Draft",
        content_markdown="Draft",
        estimated_minutes=10,
        status="draft",
        order_index=2,
    )
    db_session.add(topic)
    db_session.commit()
    content = _valid_zip(
        **{
            "problem.json": (
                '{"title":"Draft Topic ZIP","difficulty":"basic","topic_ids":["' + str(topic.id) + '"]}'
            )
        }
    )

    response = _post_zip(client, content)

    assert response.status_code == 404
    assert _error_code(response) == "TOPIC_NOT_FOUND"


def test_import_zip_rejects_non_zip_file(client) -> None:
    _register(client)

    response = _post_zip(client, b"not a zip")

    assert response.status_code == 400
    assert _error_code(response) == "ZIP_INVALID_ARCHIVE"


def test_import_zip_rejects_empty_zip(client) -> None:
    _register(client)

    response = _post_zip(client, _zip_bytes({}))

    assert response.status_code == 400
    assert _error_code(response) == "ZIP_ARCHIVE_EMPTY"


def test_import_zip_rejects_path_traversal(client) -> None:
    _register(client)

    response = _post_zip(client, _valid_zip(**{"../evil.md": "bad"}))

    assert response.status_code == 400
    assert _error_code(response) == "ZIP_PATH_NOT_ALLOWED"


def test_import_zip_rejects_multiple_top_level_directories(client) -> None:
    _register(client)
    content = _zip_bytes(
        {
            "a/problem.json": '{"title":"A","difficulty":"beginner"}',
            "a/statement.md": "A",
            "a/tests/01.in": "1",
            "a/tests/01.out": "1",
            "b/extra.md": "B",
        }
    )

    response = _post_zip(client, content)

    assert response.status_code == 400
    assert _error_code(response) == "ZIP_PATH_NOT_ALLOWED"


def test_import_zip_rejects_root_and_top_level_mix(client) -> None:
    _register(client)

    response = _post_zip(client, _valid_zip(**{"pkg/extra.md": "bad"}))

    assert response.status_code == 400
    assert _error_code(response) == "ZIP_PATH_NOT_ALLOWED"


def test_import_zip_rejects_symbolic_link_entry(client) -> None:
    _register(client)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("problem.json", '{"title":"Symlink","difficulty":"beginner"}')
        archive.writestr("statement.md", "Statement")
        archive.writestr("tests/01.in", "1")
        archive.writestr("tests/01.out", "1")
        info = zipfile.ZipInfo("solution.md")
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(info, "target")

    response = _post_zip(client, buffer.getvalue())

    assert response.status_code == 400
    assert _error_code(response) == "ZIP_PATH_NOT_ALLOWED"


def test_import_zip_rejects_disallowed_file_type(client) -> None:
    _register(client)

    response = _post_zip(client, _valid_zip(**{"notes.exe": "bad"}))

    assert response.status_code == 400
    assert _error_code(response) == "ZIP_FILE_TYPE_NOT_ALLOWED"


def test_import_zip_rejects_file_count_limit(client) -> None:
    _register(client)
    files = {
        "problem.json": '{"title":"Too Many","difficulty":"beginner"}',
        "statement.md": "Statement",
        "tests/01.in": "1",
        "tests/01.out": "1",
    }
    for index in range(60):
        files[f"extra-{index}.md"] = "extra"

    response = _post_zip(client, _zip_bytes(files))

    assert response.status_code == 400
    assert _error_code(response) == "ZIP_FILE_COUNT_EXCEEDED"


def test_import_zip_rejects_compression_ratio_limit(client) -> None:
    _register(client)

    response = _post_zip(client, _valid_zip(**{"solution.md": "x" * (400 * 1024)}))

    assert response.status_code == 400
    assert _error_code(response) == "ZIP_COMPRESSION_RATIO_EXCEEDED"


def test_import_zip_rejects_invalid_problem_json(client) -> None:
    _register(client)

    response = _post_zip(client, _valid_zip(**{"problem.json": "{bad json"}))

    assert response.status_code == 400
    assert _error_code(response) == "ZIP_INVALID_JSON"


def test_import_zip_rejects_missing_problem_json(client) -> None:
    _register(client)
    content = _zip_bytes(
        {
            "statement.md": "Statement",
            "tests/01.in": "1",
            "tests/01.out": "1",
        }
    )

    response = _post_zip(client, content)

    assert response.status_code == 400
    assert _error_code(response) == "ZIP_PROBLEM_METADATA_INVALID"


def test_import_zip_rejects_empty_statement(client) -> None:
    _register(client)

    response = _post_zip(client, _valid_zip(**{"statement.md": "   "}))

    assert response.status_code == 400
    assert _error_code(response) == "ZIP_STATEMENT_REQUIRED"


def test_import_zip_rejects_test_case_pair_mismatch(client) -> None:
    _register(client)
    content = _zip_bytes(
        {
            "problem.json": '{"title":"Mismatch","difficulty":"beginner"}',
            "statement.md": "Statement",
            "tests/01.in": "1",
        }
    )

    response = _post_zip(client, content)

    assert response.status_code == 400
    assert _error_code(response) == "ZIP_TEST_CASE_PAIR_MISMATCH"


def test_import_zip_rejects_test_case_count_limit(client) -> None:
    _register(client)
    files = {
        "problem.json": '{"title":"Too Many Cases","difficulty":"beginner"}',
        "statement.md": "Statement",
    }
    for index in range(101):
        files[f"tests/{index:03}.in"] = str(index)
        files[f"tests/{index:03}.out"] = str(index)

    response = _post_zip(client, _zip_bytes(files))

    assert response.status_code == 400
    assert _error_code(response) in {"ZIP_FILE_COUNT_EXCEEDED", "ZIP_TEST_CASE_LIMIT_EXCEEDED"}


def test_import_zip_rejects_invalid_utf8(client) -> None:
    _register(client)

    response = _post_zip(client, _valid_zip(**{"statement.md": b"\xff\xfe\xff"}))

    assert response.status_code == 400
    assert _error_code(response) == "ZIP_INVALID_ENCODING"


def test_import_zip_rejects_slug_conflict_and_rolls_back(client, db_session) -> None:
    _register(client)
    _create_problem(client)

    response = _post_zip(
        client,
        _valid_zip(
            **{
                "problem.json": (
                    '{"title":"Conflicting ZIP","slug":"manual-problem","difficulty":"beginner"}'
                )
            }
        ),
    )

    assert response.status_code == 409
    assert _error_code(response) == "PROBLEM_SLUG_ALREADY_EXISTS"
    assert db_session.scalar(select(Problem).where(Problem.title == "Conflicting ZIP")) is None


def test_import_zip_without_login_returns_auth_required(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "enable_dev_user", False)
    client.cookies.clear()

    response = _post_zip(client, _valid_zip())

    assert response.status_code == 401
    assert _error_code(response) == "AUTH_REQUIRED"
