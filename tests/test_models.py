"""Tests for sakayos.core.models — written BEFORE implementation (TDD)."""

import pytest

from sakayos.core.models import (
    MemoryBlock,
    ProcessInfo,
    SchedulerProcess,
    TimelineEntry,
)


# ── SchedulerProcess ────────────────────────────────────────────────────────


class TestSchedulerProcess:
    """Tests for the SchedulerProcess dataclass."""

    def test_valid_construction_without_priority(self):
        p = SchedulerProcess(pid="P1", arrival_time=0, burst_time=5)
        assert p.pid == "P1"
        assert p.arrival_time == 0
        assert p.burst_time == 5
        assert p.priority is None

    def test_valid_construction_with_priority(self):
        p = SchedulerProcess(pid="P2", arrival_time=3, burst_time=10, priority=2)
        assert p.pid == "P2"
        assert p.arrival_time == 3
        assert p.burst_time == 10
        assert p.priority == 2

    def test_arrival_time_zero_is_valid(self):
        p = SchedulerProcess(pid="P0", arrival_time=0, burst_time=1)
        assert p.arrival_time == 0

    def test_negative_arrival_time_raises(self):
        with pytest.raises(ValueError, match="arrival_time"):
            SchedulerProcess(pid="P1", arrival_time=-1, burst_time=5)

    def test_zero_burst_time_raises(self):
        with pytest.raises(ValueError, match="burst_time"):
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=0)

    def test_negative_burst_time_raises(self):
        with pytest.raises(ValueError, match="burst_time"):
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=-3)


# ── TimelineEntry ───────────────────────────────────────────────────────────


class TestTimelineEntry:
    """Tests for the TimelineEntry dataclass."""

    def test_valid_construction(self):
        e = TimelineEntry(pid="P1", start=0, end=5)
        assert e.pid == "P1"
        assert e.start == 0
        assert e.end == 5

    def test_duration_property(self):
        e = TimelineEntry(pid="P1", start=2, end=7)
        assert e.duration == 5

    def test_end_equal_to_start_raises(self):
        with pytest.raises(ValueError, match="end"):
            TimelineEntry(pid="P1", start=5, end=5)

    def test_end_less_than_start_raises(self):
        with pytest.raises(ValueError, match="end"):
            TimelineEntry(pid="P1", start=5, end=3)


# ── MemoryBlock ─────────────────────────────────────────────────────────────


class TestMemoryBlock:
    """Tests for the MemoryBlock dataclass."""

    def test_valid_allocated_block(self):
        b = MemoryBlock(start=0, size=128, process_id="P1")
        assert b.start == 0
        assert b.size == 128
        assert b.process_id == "P1"

    def test_valid_free_block(self):
        b = MemoryBlock(start=256, size=64, process_id=None)
        assert b.process_id is None

    def test_is_free_property_true(self):
        b = MemoryBlock(start=0, size=64, process_id=None)
        assert b.is_free is True

    def test_is_free_property_false(self):
        b = MemoryBlock(start=0, size=64, process_id="P1")
        assert b.is_free is False

    def test_negative_start_raises(self):
        with pytest.raises(ValueError, match="start"):
            MemoryBlock(start=-1, size=64, process_id=None)

    def test_zero_size_raises(self):
        with pytest.raises(ValueError, match="size"):
            MemoryBlock(start=0, size=0, process_id=None)

    def test_negative_size_raises(self):
        with pytest.raises(ValueError, match="size"):
            MemoryBlock(start=0, size=-10, process_id=None)

    def test_start_zero_is_valid(self):
        b = MemoryBlock(start=0, size=1, process_id=None)
        assert b.start == 0


# ── ProcessInfo ─────────────────────────────────────────────────────────────


class TestProcessInfo:
    """Tests for the ProcessInfo dataclass."""

    def test_valid_construction_with_username(self):
        p = ProcessInfo(
            pid=1234,
            name="python3",
            status="running",
            cpu_percent=12.5,
            memory_percent=3.2,
            username="root",
        )
        assert p.pid == 1234
        assert p.name == "python3"
        assert p.status == "running"
        assert p.cpu_percent == 12.5
        assert p.memory_percent == 3.2
        assert p.username == "root"

    def test_valid_construction_without_username(self):
        p = ProcessInfo(
            pid=42,
            name="kworker",
            status="sleeping",
            cpu_percent=0.0,
            memory_percent=0.1,
            username=None,
        )
        assert p.username is None
