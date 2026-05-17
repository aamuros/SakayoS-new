"""Dispatch Scheduler screen — interactive CPU scheduling simulation.

Users can follow a short workflow:
1. Choose an algorithm (FCFS, SJF, Round Robin, Priority).
2. Enter process data (pid, arrival_time, burst_time, [priority]).
3. Run the simulation and review summary, schedule, and metrics.
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
    TextArea,
)

from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text as RichText

from sakayos.core.models import SchedulerProcess, TimelineEntry
from sakayos.services.scheduling_service import run_scheduling_simulation
from sakayos.ui.gantt import render_gantt_table, render_gantt_text, render_metrics_table


# ── Algorithm registry ──────────────────────────────────────────────────────

_ALGORITHMS = [
    ("fcfs", "FCFS — First Come First Serve"),
    ("sjf", "SJF — Shortest Job First"),
    ("rr", "RR — Round Robin"),
    ("priority", "Priority Scheduling"),
]

_ALGO_HINT = {
    "fcfs": "Format: PID, arrival, burst. Passenger = process.",
    "sjf": "Format: PID, arrival, burst. Shorter burst times run earlier.",
    "rr": "Format: PID, arrival, burst. Add a time quantum below.",
    "priority": "Format: PID, arrival, burst, priority. Lower priority number runs first.",
}

_ALGO_EXAMPLE = {
    "fcfs": "P1, 0, 4\nP2, 2, 3\nP3, 5, 2",
    "sjf": "P1, 0, 6\nP2, 1, 2\nP3, 2, 4",
    "rr": "P1, 0, 5\nP2, 1, 3\nP3, 2, 1",
    "priority": "P1, 0, 4, 3\nP2, 0, 2, 1\nP3, 0, 3, 2",
}

_EMPTY_RESULTS_MESSAGE = (
    "No simulation yet. Choose an algorithm, load an example, "
    "or enter your own processes."
)


def _render_metrics_summary(metrics: dict[str, dict[str, float]]) -> Table:
    """Render compact average scheduling metrics."""
    table = Table(
        title="Key Metrics",
        show_header=False,
        border_style="#334155",
        box=box.SIMPLE,
        expand=True,
    )
    table.add_column("Metric", style="bold #7dd3fc")
    table.add_column("Value", justify="right")

    count = len(metrics)
    if count == 0:
        return table

    avg_turnaround = sum(m["turnaround_time"] for m in metrics.values()) / count
    avg_waiting = sum(m["waiting_time"] for m in metrics.values()) / count
    last_completion = max(m["completion_time"] for m in metrics.values())

    table.add_row("Processes", str(count))
    table.add_row("Average Turnaround", f"{avg_turnaround:.2f}")
    table.add_row("Average Waiting", f"{avg_waiting:.2f}")
    table.add_row("Finished At", str(int(last_completion)))
    return table


def _short_error_message(message: str) -> str:
    """Convert validation details into concise UI guidance."""
    if "No process data provided" in message or "No valid process lines" in message:
        return "Enter at least one process."
    if "Quantum cannot be empty" in message:
        return "Enter a time quantum for Round Robin."
    if "Quantum must be an integer" in message:
        return "Use a whole number for time quantum."
    if "Quantum must be positive" in message:
        return "Use a positive time quantum."
    if "Expected 4 fields" in message:
        return "Priority needs: PID, arrival, burst, priority."
    if "Expected at least 3 fields" in message:
        return "Use: PID, arrival, burst."
    if "Too many fields" in message:
        return "Use at most: PID, arrival, burst, priority."
    if "arrival_time must be an integer" in message:
        return "Arrival time must be a whole number."
    if "burst_time must be an integer" in message:
        return "Burst time must be a whole number."
    if "priority must be an integer" in message:
        return "Priority must be a whole number."
    if "PID cannot be empty" in message:
        return "Each process needs a PID."
    if "PID cannot contain whitespace" in message:
        return "Use a PID without spaces."
    if "PID cannot contain commas" in message:
        return "Use a PID without commas."
    if "arrival_time" in message and "<=" in message:
        return "Arrival time is too large."
    if "burst_time" in message and "<=" in message:
        return "Burst time is too large."
    if "priority" in message and "<=" in message:
        return "Priority is too large."
    if "arrival_time" in message and ">= 0" in message:
        return "Arrival time cannot be negative."
    if "burst_time" in message and "> 0" in message:
        return "Burst time must be positive."
    if "Scheduling error:" in message:
        return message.removeprefix("Scheduling error: ").strip()
    return message


# ── Dispatch Screen ────────────────────────────────────────────────────────


class DispatchScreen(Screen):
    """Interactive CPU scheduling simulation screen."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="dispatch-container", classes="screen-container"):
            # ── Title ────────────────────────────────────────────────────
            with Vertical(classes="screen-header"):
                yield Label(
                    "Dispatch Scheduler",
                    id="screen-title",
                )
                yield Label(
                    "Compare CPU scheduling policies against the same passenger queue.",
                    id="screen-description",
                    classes="short-description",
                )

            yield Static(
                "Dispatcher = scheduler. Passenger = process. Vehicle time = CPU time.",
                classes="compact-help",
            )

            # ── Algorithm selector ───────────────────────────────────────
            with Vertical(classes="form-section"):
                yield Label("Step 1: Choose algorithm", classes="section-label")
                yield Label("Scheduling Algorithm", classes="field-label")
                yield Select(
                    [(label, key) for key, label in _ALGORITHMS],
                    id="algo-select",
                    prompt="Select a scheduling algorithm...",
                )

            # ── Hint label ───────────────────────────────────────────────
            yield Label("", id="input-hint", classes="hint-label")

            # ── Process input area ───────────────────────────────────────
            with Vertical(classes="form-section"):
                yield Label("Step 2: Enter processes", classes="section-label")
                yield Label("Processes", classes="field-label")
                yield TextArea(
                    "",
                    id="process-input",
                    language="text",
                )

            # ── Quantum input (only for RR) ──────────────────────────────
            with Vertical(classes="form-section"):
                yield Label(
                    "Time Quantum",
                    id="quantum-label",
                    classes="field-label hidden",
                )
                yield Input(
                    placeholder="e.g. 2",
                    id="quantum-input",
                    classes="hidden",
                )

            # ── Action buttons ───────────────────────────────────────────
            yield Label("Step 3: Run simulation", classes="section-label")
            with Horizontal(classes="action-button-row"):
                yield Button(
                    "Run Simulation",
                    id="btn-run",
                    variant="success",
                    compact=True,
                )
                yield Button(
                    "Load Example",
                    id="btn-example",
                    variant="primary",
                    compact=True,
                )
                yield Button(
                    "Clear",
                    id="btn-clear",
                    variant="warning",
                    compact=True,
                )

            # ── Error display ────────────────────────────────────────────
            yield Static("", id="error-display", classes="hidden")

            # ── Results area ─────────────────────────────────────────────
            yield Label("Results", classes="section-label")
            yield Static(
                _EMPTY_RESULTS_MESSAGE,
                id="results-area",
                classes="result-section empty-state",
            )

            # ── Back button ──────────────────────────────────────────────
            with Center():
                yield Button("Back", id="btn-back", variant="default", compact=True)
        yield Footer()

    # ── Event handlers ──────────────────────────────────────────────────────

    def on_select_changed(self, event: Select.Changed) -> None:
        """Update UI when algorithm selection changes."""
        algo = event.value
        if algo is Select.BLANK:
            return

        # Update hint text.
        hint = self.query_one("#input-hint", Label)
        hint.update(_ALGO_HINT.get(algo, ""))

        # Show/hide quantum input.
        quantum_label = self.query_one("#quantum-label")
        quantum_input = self.query_one("#quantum-input")
        if algo == "rr":
            quantum_label.remove_class("hidden")
            quantum_input.remove_class("hidden")
        else:
            quantum_label.add_class("hidden")
            quantum_input.add_class("hidden")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        btn = event.button.id
        if btn == "btn-back":
            self.app.pop_screen()
        elif btn == "btn-run":
            self._run_simulation()
        elif btn == "btn-example":
            self._load_example()
        elif btn == "btn-clear":
            self._clear_all()

    # ── Core logic ──────────────────────────────────────────────────────────

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

    def _show_empty_state(self) -> None:
        """Display the initial results placeholder."""
        results_area = self.query_one("#results-area", Static)
        results_area.update(_EMPTY_RESULTS_MESSAGE)
        results_area.remove_class("hidden")
        results_area.add_class("empty-state")

    def _get_selected_algo(self) -> str | None:
        """Return the currently selected algorithm key, or None."""
        select = self.query_one("#algo-select", Select)
        val = select.value
        if val is Select.BLANK:
            return None
        return val

    def _run_simulation(self) -> None:
        """Validate inputs, run the scheduler, and display results."""
        self._hide_error()
        results_area = self.query_one("#results-area", Static)
        results_area.update("")
        results_area.add_class("hidden")

        # 1. Validate algorithm selection.
        algo = self._get_selected_algo()
        if algo is None:
            self._show_error("Select a scheduling algorithm first.")
            self._show_empty_state()
            return

        process_input = self.query_one("#process-input", TextArea)
        raw_text = process_input.text
        quantum_text: str | None = None
        if algo == "rr":
            quantum_text = self.query_one("#quantum-input", Input).value

        try:
            result = run_scheduling_simulation(algo, raw_text, quantum_text)
        except ValueError as e:
            self._show_error(_short_error_message(str(e)))
            self._show_empty_state()
            return

        self._display_results(
            result.algorithm,
            result.processes,
            result.timeline,
            result.metrics,
        )

    def _display_results(
        self,
        algo: str,
        processes: list[SchedulerProcess],
        timeline: list[TimelineEntry],
        metrics: dict[str, dict[str, float]],
    ) -> None:
        """Render the results into the results area."""
        results_area = self.query_one("#results-area", Static)

        # Build the input process table.
        input_table = Table(
            title="Input Processes",
            show_header=True,
            header_style="bold #f59e0b",
            border_style="#334155",
            box=box.SIMPLE,
            row_styles=["", "#94a3b8"],
            expand=True,
        )
        input_table.add_column("PID", style="bold #2dd4bf", width=8)
        input_table.add_column("Arrival", justify="right", width=10)
        input_table.add_column("Burst", justify="right", width=10)
        if algo == "priority":
            input_table.add_column("Priority", justify="right", width=10)

        for proc in processes:
            row = [proc.pid, str(proc.arrival_time), str(proc.burst_time)]
            if algo == "priority":
                row.append(str(proc.priority))
            input_table.add_row(*row)

        # Build the Gantt table and text.
        gantt_table = render_gantt_table(timeline)
        gantt_text = render_gantt_text(timeline)

        # Build the metrics table.
        pid_order = [p.pid for p in processes]
        metrics_table = render_metrics_table(metrics, pid_order=pid_order)
        summary_table = _render_metrics_summary(metrics)

        # Compose the output.
        algo_names = dict(_ALGORITHMS)
        algo_label = algo_names.get(algo, algo)

        results_area.update("")
        completion_summary = Panel(
            RichText(
                f"{algo_label} completed {len(processes)} processes.",
                style="bold #22c55e",
            ),
            title="Completion Summary",
            border_style="#22c55e",
            padding=(0, 1),
        )
        gantt_text_renderable = RichText(gantt_text, style="#e5eef4")
        gantt_group = Group(
            Panel(gantt_text_renderable, title="Gantt View", border_style="#2dd4bf"),
            gantt_table,
        )

        group = Group(
            completion_summary,
            RichText(""),
            gantt_group,
            RichText(""),
            summary_table,
            RichText(""),
            metrics_table,
            RichText(""),
            input_table,
        )

        results_area.update(group)
        results_area.remove_class("empty-state")
        results_area.remove_class("hidden")

    def _load_example(self) -> None:
        """Load example data for the selected algorithm."""
        algo = self._get_selected_algo()
        if algo is None:
            self._show_error("Select a scheduling algorithm first.")
            return

        self._hide_error()
        process_input = self.query_one("#process-input", TextArea)
        example = _ALGO_EXAMPLE.get(algo, "")
        process_input.load_text(example)

        # Set quantum for RR example.
        if algo == "rr":
            quantum_input = self.query_one("#quantum-input", Input)
            quantum_input.value = "2"

    def _clear_all(self) -> None:
        """Clear all inputs and results."""
        self._hide_error()

        process_input = self.query_one("#process-input", TextArea)
        process_input.load_text("")

        quantum_input = self.query_one("#quantum-input", Input)
        quantum_input.value = ""

        self._show_empty_state()

    def action_go_back(self) -> None:
        """Pop back to the home screen."""
        self.app.pop_screen()
