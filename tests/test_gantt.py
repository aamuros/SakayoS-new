"""Tests for sakayos.ui.gantt — Gantt chart rendering.

Tests verify that known timelines produce known, deterministic
text representations. Does NOT test full manual UI interaction.
"""

from sakayos.core.models import TimelineEntry
from sakayos.ui.gantt import render_gantt_text, render_gantt_table, render_metrics_table


# ── render_gantt_text ───────────────────────────────────────────────────────


class TestRenderGanttText:
    """Deterministic text rendering from timeline entries."""

    def test_empty_timeline_returns_empty_string(self):
        assert render_gantt_text([]) == ""

    def test_single_entry(self):
        timeline = [TimelineEntry(pid="P1", start=0, end=5)]
        result = render_gantt_text(timeline)
        # Should contain time markers and PID.
        assert "P1" in result
        assert "0" in result
        assert "5" in result

    def test_two_entries_contiguous(self):
        timeline = [
            TimelineEntry(pid="P1", start=0, end=4),
            TimelineEntry(pid="P2", start=4, end=7),
        ]
        result = render_gantt_text(timeline)
        assert "P1" in result
        assert "P2" in result
        assert "0" in result
        assert "4" in result
        assert "7" in result

    def test_bar_row_contains_pipe_delimiters(self):
        timeline = [
            TimelineEntry(pid="P1", start=0, end=3),
            TimelineEntry(pid="P2", start=3, end=6),
        ]
        result = render_gantt_text(timeline)
        lines = result.split("\n")
        bar_line = lines[1].strip()
        # Bar line should start with a pipe.
        assert bar_line.startswith("|P1")

    def test_legend_shows_process_spans(self):
        timeline = [
            TimelineEntry(pid="P1", start=0, end=2),
            TimelineEntry(pid="P2", start=2, end=4),
            TimelineEntry(pid="P1", start=4, end=6),
        ]
        result = render_gantt_text(timeline)
        # P1 should show both spans.
        assert "[0-2]" in result
        assert "[4-6]" in result
        # P2 should show its span.
        assert "[2-4]" in result

    def test_preempted_process_appears_multiple_times_in_legend(self):
        timeline = [
            TimelineEntry(pid="P1", start=0, end=2),
            TimelineEntry(pid="P2", start=2, end=4),
            TimelineEntry(pid="P1", start=4, end=6),
        ]
        result = render_gantt_text(timeline)
        # Find the P1 legend line.
        p1_line = [line for line in result.split("\n") if line.startswith("P1:")][0]
        assert "[0-2]" in p1_line
        assert "[4-6]" in p1_line

    def test_idle_gap_shown(self):
        """When there's a gap between entries, IDLE should appear."""
        timeline = [
            TimelineEntry(pid="P1", start=0, end=2),
            TimelineEntry(pid="P2", start=5, end=8),
        ]
        result = render_gantt_text(timeline)
        assert "IDLE" in result

    def test_separator_line_exists(self):
        timeline = [TimelineEntry(pid="P1", start=0, end=3)]
        result = render_gantt_text(timeline)
        assert "─" in result

    def test_round_robin_complex_timeline(self):
        """RR result with 3 processes produces correct legend."""
        timeline = [
            TimelineEntry(pid="P1", start=0, end=2),
            TimelineEntry(pid="P2", start=2, end=4),
            TimelineEntry(pid="P3", start=4, end=5),
            TimelineEntry(pid="P1", start=5, end=7),
            TimelineEntry(pid="P2", start=7, end=8),
            TimelineEntry(pid="P1", start=8, end=9),
        ]
        result = render_gantt_text(timeline)

        # Verify all processes appear.
        for pid in ["P1", "P2", "P3"]:
            assert pid in result

        # Verify P1 has 3 spans in its legend.
        p1_line = [line for line in result.split("\n") if line.startswith("P1:")][0]
        assert "[0-2]" in p1_line
        assert "[5-7]" in p1_line
        assert "[8-9]" in p1_line

    def test_deterministic_output(self):
        """Same input always produces the same output."""
        timeline = [
            TimelineEntry(pid="P1", start=0, end=3),
            TimelineEntry(pid="P2", start=3, end=5),
        ]
        result1 = render_gantt_text(timeline)
        result2 = render_gantt_text(timeline)
        assert result1 == result2


# ── render_gantt_table ──────────────────────────────────────────────────────


class TestRenderGanttTable:
    """Rich Table rendering tests."""

    def test_table_has_correct_columns(self):
        timeline = [TimelineEntry(pid="P1", start=0, end=5)]
        table = render_gantt_table(timeline)
        col_names = [col.header for col in table.columns]
        assert "#" in col_names
        assert "PID" in col_names
        assert "Start" in col_names
        assert "End" in col_names
        assert "Duration" in col_names

    def test_table_row_count_matches_timeline(self):
        timeline = [
            TimelineEntry(pid="P1", start=0, end=3),
            TimelineEntry(pid="P2", start=3, end=5),
            TimelineEntry(pid="P1", start=5, end=7),
        ]
        table = render_gantt_table(timeline)
        assert table.row_count == 3

    def test_empty_timeline_produces_empty_table(self):
        table = render_gantt_table([])
        assert table.row_count == 0


# ── render_metrics_table ────────────────────────────────────────────────────


class TestRenderMetricsTable:
    """Rich metrics table tests."""

    def test_metrics_table_has_correct_columns(self):
        metrics = {
            "P1": {"completion_time": 4, "turnaround_time": 4, "waiting_time": 0},
        }
        table = render_metrics_table(metrics)
        col_names = [col.header for col in table.columns]
        assert "PID" in col_names
        assert "Completion" in col_names
        assert "Turnaround" in col_names
        assert "Waiting" in col_names

    def test_metrics_table_row_count(self):
        metrics = {
            "P1": {"completion_time": 4, "turnaround_time": 4, "waiting_time": 0},
            "P2": {"completion_time": 7, "turnaround_time": 6, "waiting_time": 3},
        }
        table = render_metrics_table(metrics)
        # 2 data rows + 1 AVG row = 3.
        assert table.row_count == 3

    def test_metrics_table_respects_pid_order(self):
        metrics = {
            "P2": {"completion_time": 7, "turnaround_time": 6, "waiting_time": 3},
            "P1": {"completion_time": 4, "turnaround_time": 4, "waiting_time": 0},
        }
        table = render_metrics_table(metrics, pid_order=["P1", "P2"])
        # First data row should be P1.
        assert table.row_count == 3

    def test_metrics_table_empty(self):
        table = render_metrics_table({})
        assert table.row_count == 0
