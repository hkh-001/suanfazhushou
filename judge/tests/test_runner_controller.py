import subprocess
from pathlib import Path

from runner import controller
from runner.controller import normalize_output, parse_memory_kb, run_case


def test_output_normalization_ignores_line_endings_and_trailing_space() -> None:
    assert normalize_output("a  \r\nb\t\r\n\r\n") == "a\nb"


def test_empty_output_matches_single_newline() -> None:
    assert normalize_output("") == normalize_output("\n")


def test_parse_memory_kb(tmp_path: Path) -> None:
    report = tmp_path / "time.txt"
    report.write_text("Maximum resident set size (kbytes): 12345\n")
    assert parse_memory_kb(report) == 12345


def test_parse_memory_kb_returns_none_for_invalid_report(tmp_path: Path) -> None:
    report = tmp_path / "time.txt"
    report.write_text("not available")
    assert parse_memory_kb(report) is None


def test_timeout_process_group_race_still_returns_tle(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class FakeProcess:
        pid = 123

        def __init__(self) -> None:
            self.wait_count = 0

        def wait(self, timeout=None):
            self.wait_count += 1
            if self.wait_count == 1:
                raise subprocess.TimeoutExpired(cmd="python", timeout=timeout)
            return 0

    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: FakeProcess())
    monkeypatch.setattr(
        controller.os,
        "killpg",
        lambda *args: (_ for _ in ()).throw(ProcessLookupError()),
        raising=False,
    )
    monkeypatch.setattr(controller.signal, "SIGKILL", 9, raising=False)
    monkeypatch.setattr("runner.controller.read_oom_kills", lambda: 0)

    result = run_case(
        ["python", "source.py"],
        {
            "id": "case-id",
            "case_index": 1,
            "name": "race",
            "is_sample": True,
            "input_text": "",
            "expected_output_text": "",
        },
        timeout=0.01,
        process_limit=64,
        output_limit=65536,
        workspace=tmp_path,
    )

    assert result["verdict"] == "time_limit_exceeded"
