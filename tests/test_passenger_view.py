"""Tests for the Passenger Manager rendering helper.

Tests the pure render_process_table function — no live psutil calls,
no Textual screen, fully deterministic.
"""

from rich.table import Table

from sakayos.core.models import ProcessInfo
from sakayos.screens.passenger import render_process_table


# ── render_process_table ───────────────────────────────────────────────────


class TestRenderProcessTable:
    """render_process_table turns a list[ProcessInfo] into a Rich Table."""

    def test_returns_table(self):
        procs = [
            ProcessInfo(pid=1, name="init", status="sleeping",
                        cpu_percent=0.1, memory_percent=1.5, username="root"),
        ]
        result = render_process_table(procs)
        assert isinstance(result, Table)

    def test_empty_list_returns_table(self):
        result = render_process_table([])
        assert isinstance(result, Table)

    def test_table_has_expected_columns(self):
        procs = [
            ProcessInfo(pid=42, name="bash", status="running",
                        cpu_percent=2.0, memory_percent=0.5, username="user"),
        ]
        table = render_process_table(procs)
        col_names = [c.header for c in table.columns]
        # Rich Text objects — cast to str for comparison
        col_strs = [str(c) for c in col_names]
        assert "PID" in col_strs
        assert "Name" in col_strs
        assert "Status" in col_strs
        assert "CPU %" in col_strs
        assert "Mem %" in col_strs
        assert "Username" in col_strs

    def test_none_username_renders_as_na(self):
        """When username is None, the table should display 'N/A'."""
        procs = [
            ProcessInfo(pid=99, name="mystery", status="sleeping",
                        cpu_percent=0.0, memory_percent=0.0, username=None),
        ]
        table = render_process_table(procs)
        # The table should have 1 row and not crash
        assert table.row_count == 1

    def test_row_count_matches_input(self):
        procs = [
            ProcessInfo(pid=i, name=f"p{i}", status="running",
                        cpu_percent=0.0, memory_percent=0.0, username="u")
            for i in range(5)
        ]
        table = render_process_table(procs)
        assert table.row_count == 5
