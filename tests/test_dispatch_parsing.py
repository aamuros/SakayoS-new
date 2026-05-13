"""Tests for sakayos.ui.parsing — input parsing helpers.

Covers parse_process_line, parse_quantum, and parse_process_block.
"""

import pytest

from sakayos.ui.parsing import parse_process_line, parse_quantum, parse_process_block


# ── parse_process_line ──────────────────────────────────────────────────────


class TestParseProcessLine:
    """Single-line process parsing."""

    def test_comma_separated_three_fields(self):
        proc = parse_process_line("P1, 0, 5")
        assert proc.pid == "P1"
        assert proc.arrival_time == 0
        assert proc.burst_time == 5
        assert proc.priority is None

    def test_space_separated_three_fields(self):
        proc = parse_process_line("P1 0 5")
        assert proc.pid == "P1"
        assert proc.arrival_time == 0
        assert proc.burst_time == 5

    def test_comma_separated_four_fields_with_priority(self):
        proc = parse_process_line("P1, 0, 5, 2")
        assert proc.pid == "P1"
        assert proc.priority == 2

    def test_space_separated_four_fields_with_priority(self):
        proc = parse_process_line("P1 0 5 2")
        assert proc.priority == 2

    def test_simple_pid_variants_allowed(self):
        assert parse_process_line("job_1, 0, 5").pid == "job_1"
        assert parse_process_line("process-3, 0, 5").pid == "process-3"

    def test_pid_with_whitespace_raises(self):
        with pytest.raises(ValueError, match="PID.*whitespace"):
            parse_process_line("job 1, 0, 5")

    def test_require_priority_true_raises_when_missing(self):
        with pytest.raises(ValueError, match="4 fields"):
            parse_process_line("P1, 0, 5", require_priority=True)

    def test_require_priority_true_with_priority(self):
        proc = parse_process_line("P1, 0, 5, 3", require_priority=True)
        assert proc.priority == 3

    def test_empty_line_raises(self):
        with pytest.raises(ValueError, match="[Ee]mpty"):
            parse_process_line("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="[Ee]mpty"):
            parse_process_line("   ")

    def test_too_few_fields_raises(self):
        with pytest.raises(ValueError, match="Expected"):
            parse_process_line("P1, 0")

    def test_too_many_fields_raises(self):
        with pytest.raises(ValueError, match="Too many"):
            parse_process_line("P1, 0, 5, 2, extra")

    def test_non_integer_arrival_raises(self):
        with pytest.raises(ValueError, match="arrival_time"):
            parse_process_line("P1, abc, 5")

    def test_non_integer_burst_raises(self):
        with pytest.raises(ValueError, match="burst_time"):
            parse_process_line("P1, 0, abc")

    def test_non_integer_priority_raises(self):
        with pytest.raises(ValueError, match="priority"):
            parse_process_line("P1, 0, 5, abc")

    def test_huge_burst_raises(self):
        with pytest.raises(ValueError, match="burst_time.*<="):
            parse_process_line("P1, 0, 1000001")

    def test_custom_max_limits_can_be_disabled(self):
        proc = parse_process_line(
            "P1, 1000001, 1000001",
            max_arrival_time=None,
            max_burst_time=None,
        )
        assert proc.arrival_time == 1000001
        assert proc.burst_time == 1000001

    def test_negative_arrival_raises(self):
        """Validation delegated to SchedulerProcess.__post_init__."""
        with pytest.raises(ValueError, match="arrival_time"):
            parse_process_line("P1, -1, 5")

    def test_zero_burst_raises(self):
        """Validation delegated to SchedulerProcess.__post_init__."""
        with pytest.raises(ValueError, match="burst_time"):
            parse_process_line("P1, 0, 0")

    def test_extra_whitespace_handled(self):
        proc = parse_process_line("  P1 ,  0 ,  5  ")
        assert proc.pid == "P1"
        assert proc.arrival_time == 0
        assert proc.burst_time == 5


# ── parse_quantum ───────────────────────────────────────────────────────────


class TestParseQuantum:
    """Quantum value parsing."""

    def test_valid_quantum(self):
        assert parse_quantum("3") == 3

    def test_quantum_with_whitespace(self):
        assert parse_quantum("  5  ") == 5

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="[Ee]mpty"):
            parse_quantum("")

    def test_non_integer_raises(self):
        with pytest.raises(ValueError, match="integer"):
            parse_quantum("abc")

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="positive"):
            parse_quantum("0")

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="positive"):
            parse_quantum("-2")

    def test_float_raises(self):
        with pytest.raises(ValueError, match="integer"):
            parse_quantum("2.5")


# ── parse_process_block ────────────────────────────────────────────────────


class TestParseProcessBlock:
    """Multi-line process block parsing."""

    def test_multiple_processes(self):
        text = "P1, 0, 5\nP2, 1, 3\nP3, 2, 4"
        procs = parse_process_block(text)
        assert len(procs) == 3
        assert procs[0].pid == "P1"
        assert procs[1].pid == "P2"
        assert procs[2].pid == "P3"

    def test_blank_lines_skipped(self):
        text = "P1, 0, 5\n\n\nP2, 1, 3"
        procs = parse_process_block(text)
        assert len(procs) == 2

    def test_comment_lines_skipped(self):
        text = "# header line\nP1, 0, 5\n# another comment\nP2, 1, 3"
        procs = parse_process_block(text)
        assert len(procs) == 2

    def test_comments_and_blank_lines_still_work(self):
        text = "\n# processes\n\nP1, 0, 5\n\n# later\nP2, 1, 3\n"
        procs = parse_process_block(text)
        assert [proc.pid for proc in procs] == ["P1", "P2"]

    def test_empty_block_raises(self):
        with pytest.raises(ValueError, match="[Nn]o process"):
            parse_process_block("")

    def test_whitespace_only_block_raises(self):
        with pytest.raises(ValueError, match="[Nn]o process"):
            parse_process_block("   \n   \n   ")

    def test_malformed_line_reports_line_number(self):
        text = "P1, 0, 5\nP2, abc, 3"
        with pytest.raises(ValueError, match="Line 2"):
            parse_process_block(text)

    def test_malformed_line_reports_original_line_number_after_blank_lines(self):
        text = "\n# header\n\nP1, 0, 5\nP2, abc, 3"
        with pytest.raises(ValueError, match="Line 5"):
            parse_process_block(text)

    def test_require_priority_passed_through(self):
        text = "P1, 0, 5, 1\nP2, 1, 3, 2"
        procs = parse_process_block(text, require_priority=True)
        assert procs[0].priority == 1
        assert procs[1].priority == 2

    def test_priority_parsing_still_works_with_comments_and_blanks(self):
        text = "# priority data\n\nP1, 0, 5, 1\n\nP2, 1, 3, 2"
        procs = parse_process_block(text, require_priority=True)
        assert [proc.priority for proc in procs] == [1, 2]

    def test_require_priority_missing_raises(self):
        text = "P1, 0, 5\nP2, 1, 3"
        with pytest.raises(ValueError, match="Line 1"):
            parse_process_block(text, require_priority=True)

    def test_comments_only_raises(self):
        text = "# just comments\n# nothing here"
        with pytest.raises(ValueError, match="[Nn]o valid"):
            parse_process_block(text)
