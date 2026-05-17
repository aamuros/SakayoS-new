"""Passenger Manager screen — live process viewer.

Displays real OS processes via ``sakayos.core.process_reader`` as a
read-only table.  Users can sort, limit rows, and refresh.
No process modification is performed.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Label,
    Select,
    Static,
)

from rich import box
from rich.table import Table
from rich.text import Text

from sakayos.core.process_reader import list_processes
from sakayos.core.models import ProcessInfo

_SORT_OPTIONS = [
    ("PID (ascending)", "pid"),
    ("CPU % (descending)", "cpu"),
    ("Memory % (descending)", "memory"),
    ("Name (A-Z)", "name"),
]

_LIMIT_OPTIONS = [
    ("10 rows", 10),
    ("25 rows", 25),
    ("50 rows", 50),
    ("All", None),
]

_SORT_LABELS = {key: label for label, key in _SORT_OPTIONS}
_LIMIT_LABELS = {value: label for label, value in _LIMIT_OPTIONS}


def render_process_table(processes: list[ProcessInfo]) -> Table:
    """Render a list of ProcessInfo as a Rich Table.

    This is a pure helper — no side effects, no psutil calls.
    """
    table = Table(
        title="Processes",
        show_header=True,
        header_style="bold #7dd3fc",
        border_style="#334155",
        box=box.SIMPLE,
        row_styles=["", "#94a3b8"],
        expand=True,
    )
    table.add_column("PID", justify="right", width=8, style="#2dd4bf")
    table.add_column("Name", width=24, style="#e5eef4")
    table.add_column("Status", width=12)
    table.add_column("CPU %", justify="right", width=10)
    table.add_column("Mem %", justify="right", width=10)
    table.add_column("Username", width=16, style="#cbd5e1")

    for proc in processes:
        # Colour-code status
        status_style = "#22c55e" if proc.status == "running" else "#64748b"
        # Colour-code high CPU / memory
        cpu_style = "bold #fb7185" if proc.cpu_percent >= 50.0 else ""
        mem_style = "bold #fb7185" if proc.memory_percent >= 50.0 else ""

        table.add_row(
            str(proc.pid),
            proc.name,
            Text(proc.status, style=status_style),
            Text(f"{proc.cpu_percent:.1f}", style=cpu_style),
            Text(f"{proc.memory_percent:.1f}", style=mem_style),
            proc.username or "N/A",
        )

    return table


class PassengerScreen(Screen):
    """Live process viewer screen."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="passenger-container", classes="screen-container"):
            # ── Title ────────────────────────────────────────────────────
            with Vertical(classes="screen-header"):
                yield Label(
                    "Passenger Manager",
                    id="screen-title",
                )
                yield Label(
                    "Read-only process monitor for the current host.",
                    id="screen-description",
                    classes="short-description",
                )

            yield Static(
                "Live process data. Sort, limit, and refresh without modifying the OS.",
                classes="compact-help",
            )

            # ── Controls ─────────────────────────────────────────────────
            yield Label("Controls", classes="section-label")
            with Horizontal(classes="toolbar form-section"):
                yield Label("Sort by:", classes="field-label")
                yield Select(
                    [(label, key) for label, key in _SORT_OPTIONS],
                    id="select-sort",
                    prompt="Sort by...",
                    value="pid",
                )
                yield Label("Show:", classes="field-label")
                yield Select(
                    [(label, val) for label, val in _LIMIT_OPTIONS],
                    id="select-limit",
                    prompt="Row limit...",
                    value=25,
                )
                yield Button(
                    "Refresh",
                    id="btn-refresh",
                    variant="success",
                    compact=True,
                )

            yield Static("", id="status-line", classes="status-line hidden")

            # ── Error display ────────────────────────────────────────────
            yield Static("", id="error-display", classes="hidden")

            # ── Results area ─────────────────────────────────────────────
            yield Label("Process Table", classes="section-label")
            yield Static("", id="results-area", classes="result-section hidden")

            # ── Back button ──────────────────────────────────────────────
            with Center():
                yield Button("Back", id="btn-back", variant="default", compact=True)
        yield Footer()

    # ── Lifecycle ────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        """Load process data as soon as the screen is shown."""
        self._load_processes()

    # ── Event handlers ──────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        btn_id = event.button.id
        if btn_id == "btn-back":
            self.action_go_back()
        elif btn_id == "btn-refresh":
            self._load_processes()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Reload data when sort or limit changes."""
        self._load_processes()

    # ── Actions ──────────────────────────────────────────────────────────

    def action_go_back(self) -> None:
        """Pop back to the home screen."""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Refresh process list (keyboard shortcut)."""
        self._load_processes()

    # ── Core logic ──────────────────────────────────────────────────────

    def _show_error(self, message: str) -> None:
        """Display an error message."""
        error_display = self.query_one("#error-display", Static)
        error_display.update(f"[bold red]Error:[/] {message}")
        error_display.remove_class("hidden")

    def _hide_error(self) -> None:
        """Hide the error display."""
        error_display = self.query_one("#error-display", Static)
        error_display.update("")
        error_display.add_class("hidden")

    def _load_processes(self) -> None:
        """Fetch process data from process_reader and display it."""
        self._hide_error()
        results_area = self.query_one("#results-area", Static)
        status_line = self.query_one("#status-line", Static)

        # Read sort selection
        sort_select = self.query_one("#select-sort", Select)
        sort_by = sort_select.value if sort_select.value is not Select.BLANK else "pid"

        # Read limit selection
        limit_select = self.query_one("#select-limit", Select)
        limit = limit_select.value if limit_select.value is not Select.BLANK else 25

        try:
            processes = list_processes(sort_by=str(sort_by), limit=limit)
        except ValueError as e:
            self._show_error(str(e))
            results_area.update(
                "[bold]Process list unavailable.[/]\n"
                "[dim]Adjust the controls and refresh.[/]"
            )
            results_area.add_class("empty-state")
            results_area.remove_class("hidden")
            status_line.update("")
            status_line.add_class("hidden")
            return
        except Exception as e:
            self._show_error(f"Could not read processes: {e}")
            results_area.update(
                "[bold]Process list unavailable.[/]\n"
                "[dim]Refresh after checking process access on this system.[/]"
            )
            results_area.add_class("empty-state")
            results_area.remove_class("hidden")
            status_line.update("")
            status_line.add_class("hidden")
            return

        if not processes:
            results_area.update(
                "[bold]No accessible processes found.[/]\n"
                "[dim]Refresh or try a smaller limit if process data is restricted.[/]"
            )
            results_area.add_class("empty-state")
            results_area.remove_class("hidden")
            status_line.update("")
            status_line.add_class("hidden")
            return

        table = render_process_table(processes)

        from rich.console import Group

        status_line.update(
            f"Showing {len(processes)} processes | "
            f"Sorted by {_SORT_LABELS.get(str(sort_by), str(sort_by))} | "
            f"Limit {_LIMIT_LABELS.get(limit, limit)}"
        )
        status_line.remove_class("hidden")

        group = Group(table)
        results_area.update(group)
        results_area.remove_class("empty-state")
        results_area.remove_class("hidden")
