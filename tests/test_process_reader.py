"""Tests for sakayos.core.process_reader — the Passenger Manager process reader.

Every test mocks psutil.process_iter so results are deterministic and
independent of the host system's actual process list.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import psutil
import pytest

from sakayos.core.models import ProcessInfo
from sakayos.core.process_reader import list_processes


# ── helpers ─────────────────────────────────────────────────────────────────


def _make_mock_process(
    pid: int | None,
    name: str | None = "test",
    status: str | None = "running",
    cpu_percent: float | None = 0.0,
    memory_percent: float | None = 0.0,
    username: str | None = "user",
) -> MagicMock:
    """Build a mock object that behaves like a psutil.Process.

    The mock exposes an ``info`` attribute compatible with the dict
    returned by ``psutil.process_iter(attrs=[...])``'s items.
    """
    proc = MagicMock()
    proc.info = {
        "pid": pid,
        "name": name,
        "status": status,
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "username": username,
    }
    return proc


def _make_mock_process_from_info(info: dict) -> MagicMock:
    """Build a mock process with a custom psutil info dict."""
    proc = MagicMock()
    proc.info = info
    return proc


def _make_raising_process(exception_cls: type) -> object:
    """Build a mock process whose ``info`` access raises *exception_cls*."""

    class RaisingProcess:
        @property
        def info(self) -> dict:
            raise exception_cls(pid=0)

    return RaisingProcess()


def _make_unexpected_raising_process() -> object:
    """Build a mock process whose ``info`` access raises an unexpected error."""

    class RaisingProcess:
        @property
        def info(self) -> dict:
            raise RuntimeError("boom")

    return RaisingProcess()


# ── 1. list_processes returns ProcessInfo objects ───────────────────────────


@patch("sakayos.core.process_reader.psutil")
def test_returns_process_info_objects(mock_psutil: MagicMock) -> None:
    """list_processes should return a list of ProcessInfo dataclass instances."""
    mock_psutil.process_iter.return_value = [
        _make_mock_process(pid=1, name="init", status="sleeping",
                           cpu_percent=0.1, memory_percent=1.5, username="root"),
        _make_mock_process(pid=2, name="bash", status="running",
                           cpu_percent=0.5, memory_percent=2.0, username="user"),
    ]
    mock_psutil.AccessDenied = psutil.AccessDenied
    mock_psutil.NoSuchProcess = psutil.NoSuchProcess
    mock_psutil.ZombieProcess = psutil.ZombieProcess

    result = list_processes()

    assert len(result) == 2
    assert all(isinstance(p, ProcessInfo) for p in result)
    assert result[0].pid == 1
    assert result[0].name == "init"
    assert result[0].status == "sleeping"
    assert result[0].cpu_percent == 0.1
    assert result[0].memory_percent == 1.5
    assert result[0].username == "root"


# ── 2. Exceptions are gracefully skipped ────────────────────────────────────


@patch("sakayos.core.process_reader.psutil")
def test_skips_access_denied(mock_psutil: MagicMock) -> None:
    """Processes that raise AccessDenied should be silently skipped."""
    mock_psutil.process_iter.return_value = [
        _make_raising_process(psutil.AccessDenied),
        _make_mock_process(pid=10, name="safe"),
    ]
    mock_psutil.AccessDenied = psutil.AccessDenied
    mock_psutil.NoSuchProcess = psutil.NoSuchProcess
    mock_psutil.ZombieProcess = psutil.ZombieProcess

    result = list_processes()

    assert len(result) == 1
    assert result[0].pid == 10


@patch("sakayos.core.process_reader.psutil")
def test_skips_no_such_process(mock_psutil: MagicMock) -> None:
    """Processes that raise NoSuchProcess should be silently skipped."""
    mock_psutil.process_iter.return_value = [
        _make_raising_process(psutil.NoSuchProcess),
        _make_mock_process(pid=20, name="alive"),
    ]
    mock_psutil.AccessDenied = psutil.AccessDenied
    mock_psutil.NoSuchProcess = psutil.NoSuchProcess
    mock_psutil.ZombieProcess = psutil.ZombieProcess

    result = list_processes()

    assert len(result) == 1
    assert result[0].pid == 20


@patch("sakayos.core.process_reader.psutil")
def test_skips_zombie_process(mock_psutil: MagicMock) -> None:
    """Processes that raise ZombieProcess should be silently skipped."""
    mock_psutil.process_iter.return_value = [
        _make_raising_process(psutil.ZombieProcess),
        _make_mock_process(pid=30, name="healthy"),
    ]
    mock_psutil.AccessDenied = psutil.AccessDenied
    mock_psutil.NoSuchProcess = psutil.NoSuchProcess
    mock_psutil.ZombieProcess = psutil.ZombieProcess

    result = list_processes()

    assert len(result) == 1
    assert result[0].pid == 30


@patch("sakayos.core.process_reader.psutil")
def test_skips_unexpected_process_exception(mock_psutil: MagicMock) -> None:
    """Unexpected per-process errors should not crash the whole listing."""
    mock_psutil.process_iter.return_value = [
        _make_unexpected_raising_process(),
        _make_mock_process(pid=40, name="safe"),
    ]
    mock_psutil.AccessDenied = psutil.AccessDenied
    mock_psutil.NoSuchProcess = psutil.NoSuchProcess
    mock_psutil.ZombieProcess = psutil.ZombieProcess

    result = list_processes()

    assert len(result) == 1
    assert result[0].pid == 40


# ── 2b. Missing and None fields are handled defensively ────────────────────


@patch("sakayos.core.process_reader.psutil")
def test_missing_fields_use_safe_defaults(mock_psutil: MagicMock) -> None:
    mock_psutil.process_iter.return_value = [
        _make_mock_process_from_info({"pid": 101}),
    ]
    mock_psutil.AccessDenied = psutil.AccessDenied
    mock_psutil.NoSuchProcess = psutil.NoSuchProcess
    mock_psutil.ZombieProcess = psutil.ZombieProcess

    result = list_processes()

    assert len(result) == 1
    assert result[0] == ProcessInfo(
        pid=101,
        name="unknown",
        status="unknown",
        cpu_percent=0.0,
        memory_percent=0.0,
        username=None,
    )


@patch("sakayos.core.process_reader.psutil")
def test_none_fields_use_safe_defaults(mock_psutil: MagicMock) -> None:
    mock_psutil.process_iter.return_value = [
        _make_mock_process(
            pid=102,
            name=None,
            status=None,
            cpu_percent=None,
            memory_percent=None,
            username=None,
        ),
    ]
    mock_psutil.AccessDenied = psutil.AccessDenied
    mock_psutil.NoSuchProcess = psutil.NoSuchProcess
    mock_psutil.ZombieProcess = psutil.ZombieProcess

    result = list_processes()

    assert len(result) == 1
    assert result[0] == ProcessInfo(
        pid=102,
        name="unknown",
        status="unknown",
        cpu_percent=0.0,
        memory_percent=0.0,
        username=None,
    )


@patch("sakayos.core.process_reader.psutil")
def test_missing_or_none_pid_is_skipped(mock_psutil: MagicMock) -> None:
    mock_psutil.process_iter.return_value = [
        _make_mock_process_from_info({"name": "missing-pid"}),
        _make_mock_process(pid=None, name="none-pid"),
        _make_mock_process(pid=103, name="valid"),
    ]
    mock_psutil.AccessDenied = psutil.AccessDenied
    mock_psutil.NoSuchProcess = psutil.NoSuchProcess
    mock_psutil.ZombieProcess = psutil.ZombieProcess

    result = list_processes()

    assert [p.pid for p in result] == [103]


# ── 3. sort_by="pid" — ascending ───────────────────────────────────────────


@patch("sakayos.core.process_reader.psutil")
def test_sort_by_pid_ascending(mock_psutil: MagicMock) -> None:
    mock_psutil.process_iter.return_value = [
        _make_mock_process(pid=50),
        _make_mock_process(pid=10),
        _make_mock_process(pid=30),
    ]
    mock_psutil.AccessDenied = psutil.AccessDenied
    mock_psutil.NoSuchProcess = psutil.NoSuchProcess
    mock_psutil.ZombieProcess = psutil.ZombieProcess

    result = list_processes(sort_by="pid")

    assert [p.pid for p in result] == [10, 30, 50]


# ── 4. sort_by="cpu" — descending ──────────────────────────────────────────


@patch("sakayos.core.process_reader.psutil")
def test_sort_by_cpu_descending(mock_psutil: MagicMock) -> None:
    mock_psutil.process_iter.return_value = [
        _make_mock_process(pid=1, cpu_percent=1.0),
        _make_mock_process(pid=2, cpu_percent=5.0),
        _make_mock_process(pid=3, cpu_percent=3.0),
    ]
    mock_psutil.AccessDenied = psutil.AccessDenied
    mock_psutil.NoSuchProcess = psutil.NoSuchProcess
    mock_psutil.ZombieProcess = psutil.ZombieProcess

    result = list_processes(sort_by="cpu")

    assert [p.cpu_percent for p in result] == [5.0, 3.0, 1.0]


@patch("sakayos.core.process_reader.psutil")
def test_sort_by_cpu_is_stable_for_equal_values(mock_psutil: MagicMock) -> None:
    mock_psutil.process_iter.return_value = [
        _make_mock_process(pid=1, name="first", cpu_percent=2.0),
        _make_mock_process(pid=2, name="second", cpu_percent=2.0),
        _make_mock_process(pid=3, name="third", cpu_percent=1.0),
    ]
    mock_psutil.AccessDenied = psutil.AccessDenied
    mock_psutil.NoSuchProcess = psutil.NoSuchProcess
    mock_psutil.ZombieProcess = psutil.ZombieProcess

    result = list_processes(sort_by="cpu")

    assert [p.name for p in result] == ["first", "second", "third"]


# ── 5. sort_by="memory" — descending ───────────────────────────────────────


@patch("sakayos.core.process_reader.psutil")
def test_sort_by_memory_descending(mock_psutil: MagicMock) -> None:
    mock_psutil.process_iter.return_value = [
        _make_mock_process(pid=1, memory_percent=2.0),
        _make_mock_process(pid=2, memory_percent=8.0),
        _make_mock_process(pid=3, memory_percent=4.0),
    ]
    mock_psutil.AccessDenied = psutil.AccessDenied
    mock_psutil.NoSuchProcess = psutil.NoSuchProcess
    mock_psutil.ZombieProcess = psutil.ZombieProcess

    result = list_processes(sort_by="memory")

    assert [p.memory_percent for p in result] == [8.0, 4.0, 2.0]


# ── 6. sort_by="name" — alphabetical ascending ─────────────────────────────


@patch("sakayos.core.process_reader.psutil")
def test_sort_by_name_alphabetical(mock_psutil: MagicMock) -> None:
    mock_psutil.process_iter.return_value = [
        _make_mock_process(pid=1, name="zsh"),
        _make_mock_process(pid=2, name="bash"),
        _make_mock_process(pid=3, name="fish"),
    ]
    mock_psutil.AccessDenied = psutil.AccessDenied
    mock_psutil.NoSuchProcess = psutil.NoSuchProcess
    mock_psutil.ZombieProcess = psutil.ZombieProcess

    result = list_processes(sort_by="name")

    assert [p.name for p in result] == ["bash", "fish", "zsh"]


# ── 7. Invalid sort_by raises ValueError ───────────────────────────────────


def test_invalid_sort_by_raises_value_error() -> None:
    with pytest.raises(ValueError, match="sort_by"):
        list_processes(sort_by="invalid_key")


# ── 8. limit restricts result length ───────────────────────────────────────


@patch("sakayos.core.process_reader.psutil")
def test_limit_restricts_result_length(mock_psutil: MagicMock) -> None:
    mock_psutil.process_iter.return_value = [
        _make_mock_process(pid=i) for i in range(1, 11)
    ]
    mock_psutil.AccessDenied = psutil.AccessDenied
    mock_psutil.NoSuchProcess = psutil.NoSuchProcess
    mock_psutil.ZombieProcess = psutil.ZombieProcess

    result = list_processes(limit=3)

    assert len(result) == 3


# ── 9. limit <= 0 raises ValueError ────────────────────────────────────────


@pytest.mark.parametrize("bad_limit", [0, -1, -100])
def test_limit_zero_or_negative_raises_value_error(bad_limit: int) -> None:
    with pytest.raises(ValueError, match="limit"):
        list_processes(limit=bad_limit)


# ── 10. Optional CPU sampling ──────────────────────────────────────────────


@patch("sakayos.core.process_reader.time.sleep")
@patch("sakayos.core.process_reader.psutil")
def test_sample_cpu_reads_cpu_after_interval(
    mock_psutil: MagicMock,
    mock_sleep: MagicMock,
) -> None:
    proc = _make_mock_process(pid=1, name="sampled", cpu_percent=0.0)
    proc.cpu_percent.side_effect = [0.0, 12.5]
    mock_psutil.process_iter.return_value = [proc]
    mock_psutil.AccessDenied = psutil.AccessDenied
    mock_psutil.NoSuchProcess = psutil.NoSuchProcess
    mock_psutil.ZombieProcess = psutil.ZombieProcess

    result = list_processes(sample_cpu=True, sample_interval=0.01)

    assert result[0].cpu_percent == 12.5
    assert proc.cpu_percent.call_count == 2
    proc.cpu_percent.assert_any_call(interval=None)
    mock_sleep.assert_called_once_with(0.01)


def test_negative_sample_interval_raises_value_error() -> None:
    with pytest.raises(ValueError, match="sample_interval"):
        list_processes(sample_cpu=True, sample_interval=-0.1)
