"""Passenger Manager screen — live process viewer.

Displays real OS processes via ``sakayos.core.process_reader`` as a
read-only table.  Users can sort, limit rows, and refresh.
No process modification is performed.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Label,
    Select,
    Static,
)

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


def render_process_table(processes: list[ProcessInfo]) -> Table:
    """Render a list of ProcessInfo as a Rich Table.

    This is a pure helper — no side effects, no psutil calls.
    """
    table = Table(
        title="🧑‍🤝‍🧑 Passengers on the Bus (Processes)",
        show_header=True,
        header_style="bold bright_yellow",
        border_style="dim",
        expand=True,
    )
    table.add_column("PID", justify="right", width=8, style="bold")
    table.add_column("Name", width=24)
    table.add_column("Status", width=12)
    table.add_column("CPU %", justify="right", width=10)
    table.add_column("Mem %", justify="right", width=10)
    table.add_column("Username", width=16)

    for proc in processes:
        # Colour-code status
        status_style = "bright_green" if proc.status == "running" else "dim"
        # Colour-code high CPU / memory
        cpu_style = "bold bright_red" if proc.cpu_percent >= 50.0 else ""
        mem_style = "bold bright_red" if proc.memory_percent >= 50.0 else ""

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
        with VerticalScroll(id="passenger-container"):
            # ── Title ────────────────────────────────────────────────────
            with Center():
                yield Label(
                    "🧑‍🤝‍🧑  Passenger Manager  (Process Viewer)",
                    id="screen-title",
                )
            with Center():
                yield Label(
                    "Every running process on your system is a passenger on "
                    "the bus. This read-only view shows who is currently "
                    "riding — their PID, name, CPU and memory usage, and "
                    "status. No processes are modified.",
                    id="screen-description",
                )

            # ── Help Panel ────────────────────────────────────────────────
            yield Static(
                "[bold bright_cyan]🗺 Analogy Guide[/]\n"
                "  Passenger = [bold]Process[/] (a running program)\n"
                "  Boarding the bus = Process is [bold]running[/]\n"
                "  Waiting at the terminal = Process is [bold]sleeping/waiting[/]\n"
                "  PID = Passenger's ticket number\n"
                "  CPU % = How much of the vehicle's engine the passenger uses\n"
                "  Mem % = How many seats the passenger occupies",
                id="help-panel",
            )

            # ── Controls ─────────────────────────────────────────────────
            with Horizontal(classes="form-row"):
                yield Label("Sort by:", classes="field-label")
                yield Select(
                    [(label, key) for label, key in _SORT_OPTIONS],
                    id="select-sort",
                    prompt="Sort by…",
                    value="pid",
                )
                yield Label("Show:", classes="field-label")
                yield Select(
                    [(label, val) for label, val in _LIMIT_OPTIONS],
                    id="select-limit",
                    prompt="Row limit…",
                    value=25,
                )

            with Center():
                with Horizontal(classes="btn-group"):
                    yield Button(
                        "🔄  Refresh",
                        id="btn-refresh",
                        variant="success",
                    )

            # ── Error display ────────────────────────────────────────────
            yield Static("", id="error-display", classes="hidden")

            # ── Results area ─────────────────────────────────────────────
            yield Static("", id="results-area", classes="hidden")

            # ── Back button ──────────────────────────────────────────────
            with Center():
                yield Button("← Back to Home", id="btn-back", variant="default")
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
        error_display.update(f"[bold red]⚠ Error:[/] {message}")
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
            return
        except Exception as e:
            self._show_error(f"Unexpected error reading processes: {e}")
            return

        if not processes:
            results_area.update(
                "[bold yellow]ℹ No accessible processes found.[/]\n"
                "This may happen if psutil cannot read process data on "
                "this system."
            )
            results_area.remove_class("hidden")
            return

        table = render_process_table(processes)

        from rich.console import Group

        count_text = Text(
            f"\nShowing {len(processes)} process(es)  •  "
            f"Sorted by: {sort_by}  •  "
            f"Limit: {limit if limit is not None else 'All'}\n",
            style="dim",
        )

        group = Group(count_text, table)
        results_area.update(group)
        results_area.remove_class("hidden")
