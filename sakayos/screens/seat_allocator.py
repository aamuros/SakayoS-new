"""Seat Allocator screen — memory allocation simulation.

Users can:
1. Initialize a memory pool with a specific size.
2. Choose an allocation strategy (First Fit, Best Fit, Worst Fit).
3. Allocate memory blocks for specific process IDs.
4. Deallocate memory by process ID.
5. View memory visualizer, block list, and fragmentation metrics.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
)
from rich.console import Group
from rich.panel import Panel
from rich.text import Text

from sakayos.core.memory import MemoryAllocator
from sakayos.ui.memory_view import (
    render_memory_bar,
    render_memory_table,
    render_fragmentation_summary,
)
from sakayos.ui.parsing import parse_memory_size, parse_process_id

_STRATEGIES = [
    ("First Fit", "first_fit"),
    ("Best Fit", "best_fit"),
    ("Worst Fit", "worst_fit"),
]


class SeatAllocatorScreen(Screen):
    """Memory allocation simulation screen."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.allocator: MemoryAllocator | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="seat-container"):
            # ── Title ────────────────────────────────────────────────────
            with Center():
                yield Label(
                    "💺  Seat Allocator",
                    id="screen-title",
                )
            with Center():
                yield Label(
                    "Simulate memory allocation. Initialize memory, choose a strategy, "
                    "then allocate and deallocate blocks. This module demonstrates "
                    "fragmentation in contiguous memory allocation.",
                    id="screen-description",
                )

            # ── Initialization Section ───────────────────────────────────
            with Horizontal(classes="form-row"):
                yield Label("Total Memory Size:", classes="field-label")
                yield Input(placeholder="e.g. 1024", id="input-mem-size", classes="short-input")
                yield Button("Initialize", id="btn-init", variant="primary")

            yield Static("", id="error-display", classes="hidden")

            # ── Action Section (hidden until init) ───────────────────────
            with Vertical(id="action-section", classes="hidden"):
                yield Label("Allocation Strategy", classes="field-label")
                yield Select(
                    [(label, key) for label, key in _STRATEGIES],
                    id="select-strategy",
                    prompt="Select Strategy...",
                    value="first_fit"
                )

                with Horizontal(classes="form-row"):
                    yield Label("Process ID:", classes="field-label")
                    yield Input(placeholder="e.g. P1", id="input-pid", classes="short-input")
                    yield Label("Size:", classes="field-label")
                    yield Input(placeholder="e.g. 100", id="input-alloc-size", classes="short-input")

                with Center():
                    with Horizontal(classes="btn-group"):
                        yield Button("Allocate", id="btn-alloc", variant="success")
                        yield Button("Deallocate", id="btn-dealloc", variant="warning")

            # ── Results Area ─────────────────────────────────────────────
            yield Static("", id="results-area", classes="hidden")

            with Center():
                yield Button("← Back to Home", id="btn-back", variant="default")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle the buttons."""
        btn_id = event.button.id
        if btn_id == "btn-back":
            self.action_go_back()
        elif btn_id == "btn-init":
            self._initialize_memory()
        elif btn_id == "btn-alloc":
            self._allocate_memory()
        elif btn_id == "btn-dealloc":
            self._deallocate_memory()

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

    def _initialize_memory(self) -> None:
        self._hide_error()
        raw_size = self.query_one("#input-mem-size", Input).value
        try:
            size = parse_memory_size(raw_size)
        except ValueError as e:
            self._show_error(str(e))
            return

        self.allocator = MemoryAllocator(total_size=size)
        self.query_one("#action-section").remove_class("hidden")
        self._update_display()

    def _allocate_memory(self) -> None:
        self._hide_error()
        if self.allocator is None:
            self._show_error("Please initialize memory first.")
            return

        strategy = self.query_one("#select-strategy", Select).value
        if strategy is Select.BLANK:
            self._show_error("Please select a strategy.")
            return

        raw_pid = self.query_one("#input-pid", Input).value
        raw_size = self.query_one("#input-alloc-size", Input).value

        try:
            pid = parse_process_id(raw_pid)
            size = parse_memory_size(raw_size)
        except ValueError as e:
            self._show_error(str(e))
            return

        try:
            success = self.allocator.allocate(pid, size, str(strategy))
        except ValueError as e:
            self._show_error(str(e))
            return

        if not success:
            self._show_error(f"Failed to allocate {size} units for {pid} (No suitable block found).")
            return

        # Clear inputs on success
        self.query_one("#input-pid", Input).value = ""
        self.query_one("#input-alloc-size", Input).value = ""
        self._update_display()

    def _deallocate_memory(self) -> None:
        self._hide_error()
        if self.allocator is None:
            self._show_error("Please initialize memory first.")
            return

        raw_pid = self.query_one("#input-pid", Input).value
        try:
            pid = parse_process_id(raw_pid)
        except ValueError as e:
            self._show_error(str(e))
            return

        success = self.allocator.deallocate(pid)
        if not success:
            self._show_error(f"Failed to deallocate {pid} (Process not found).")
            return

        # Clear inputs on success
        self.query_one("#input-pid", Input).value = ""
        self._update_display()

    def _update_display(self) -> None:
        """Update the results area with current memory state."""
        if self.allocator is None:
            return

        results_area = self.query_one("#results-area", Static)
        
        blocks = self.allocator.get_blocks()
        summary = self.allocator.get_fragmentation_summary()

        bar_text = render_memory_bar(blocks)
        table = render_memory_table(blocks)
        summary_table = render_fragmentation_summary(summary)

        group = Group(
            Panel(Text(bar_text, style="bright_cyan"), title="Memory Visualizer", border_style="cyan"),
            Text(""),
            table,
            Text(""),
            summary_table
        )

        results_area.update(group)
        results_area.remove_class("hidden")

    def action_go_back(self) -> None:
        """Pop back to the home screen."""
        self.app.pop_screen()

