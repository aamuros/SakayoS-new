"""Dispatch Scheduler screen — interactive CPU scheduling simulation.

Users can:
1. Choose an algorithm (FCFS, SJF, Round Robin, Priority).
2. Enter process data (pid, arrival_time, burst_time, [priority]).
3. Optionally enter a quantum (Round Robin only).
4. Run the simulation and view:
   - Process input table
   - Gantt timeline
   - Metrics table (completion, turnaround, waiting time)
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

from rich.table import Table
from rich.text import Text

from sakayos.core.models import SchedulerProcess, TimelineEntry
from sakayos.core.scheduling import (
    calculate_metrics,
    schedule_fcfs,
    schedule_priority,
    schedule_round_robin,
    schedule_sjf,
)
from sakayos.ui.gantt import render_gantt_table, render_gantt_text, render_metrics_table
from sakayos.ui.parsing import parse_process_block, parse_quantum


# ── Algorithm registry ──────────────────────────────────────────────────────

_ALGORITHMS = [
    ("fcfs", "FCFS — First Come First Serve"),
    ("sjf", "SJF — Shortest Job First"),
    ("rr", "RR — Round Robin"),
    ("priority", "Priority Scheduling"),
]

_ALGO_HINT = {
    "fcfs": "Enter processes: pid, arrival_time, burst_time (one per line)",
    "sjf": "Enter processes: pid, arrival_time, burst_time (one per line)",
    "rr": "Enter processes: pid, arrival_time, burst_time (one per line)",
    "priority": "Enter processes: pid, arrival_time, burst_time, priority (one per line)",
}

_ALGO_EXAMPLE = {
    "fcfs": "P1, 0, 4\nP2, 2, 3\nP3, 5, 2",
    "sjf": "P1, 0, 6\nP2, 1, 2\nP3, 2, 4",
    "rr": "P1, 0, 5\nP2, 1, 3\nP3, 2, 1",
    "priority": "P1, 0, 4, 3\nP2, 0, 2, 1\nP3, 0, 3, 2",
}


# ── Dispatch Screen ────────────────────────────────────────────────────────


class DispatchScreen(Screen):
    """Interactive CPU scheduling simulation screen."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="dispatch-container"):
            # ── Title ────────────────────────────────────────────────────
            with Center():
                yield Label(
                    "🚏  Dispatch Scheduler  (CPU Scheduling)",
                    id="screen-title",
                )
            with Center():
                yield Label(
                    "The dispatcher decides which passenger (process) gets to "
                    "ride the vehicle (CPU) next. Choose a dispatching "
                    "(scheduling) algorithm, enter passengers waiting in the "
                    "terminal line (ready queue), and run the simulation.",
                    id="screen-description",
                )

            # ── Help Panel ────────────────────────────────────────────────
            yield Static(
                "[bold bright_cyan]🗺 Analogy Guide[/]\n"
                "  Passenger = [bold]Process[/] (a program waiting for CPU time)\n"
                "  Vehicle = [bold]CPU[/] (the processor that runs code)\n"
                "  Terminal line = [bold]Ready Queue[/] (processes waiting to run)\n"
                "  Dispatching = [bold]Scheduling[/] (choosing who goes next)\n"
                "  Arrival time = When the passenger reaches the terminal\n"
                "  Burst time = How long the passenger rides the vehicle",
                id="help-panel",
            )

            # ── Algorithm selector ───────────────────────────────────────
            yield Label("Dispatching Algorithm (Scheduling)", classes="field-label")
            yield Select(
                [(label, key) for key, label in _ALGORITHMS],
                id="algo-select",
                prompt="Select a scheduling algorithm…",
            )

            # ── Hint label ───────────────────────────────────────────────
            yield Label("", id="input-hint", classes="hint-label")

            # ── Process input area ───────────────────────────────────────
            yield Label("Passenger Data (Process Data)", classes="field-label")
            yield TextArea(
                "",
                id="process-input",
                language="text",
            )

            # ── Quantum input (only for RR) ──────────────────────────────
            yield Label(
                "Time Quantum (Round Robin only)",
                id="quantum-label",
                classes="field-label hidden",
            )
            yield Input(
                placeholder="e.g. 2",
                id="quantum-input",
                classes="hidden",
            )

            # ── Action buttons ───────────────────────────────────────────
            with Center():
                with Horizontal(classes="btn-group"):
                    yield Button(
                        "▶  Run Simulation",
                        id="btn-run",
                        variant="success",
                    )
                    yield Button(
                        "📋  Load Example",
                        id="btn-example",
                        variant="primary",
                    )
                    yield Button(
                        "🗑  Clear",
                        id="btn-clear",
                        variant="warning",
                    )

            # ── Error display ────────────────────────────────────────────
            yield Static("", id="error-display", classes="hidden")

            # ── Results area ─────────────────────────────────────────────
            yield Static("", id="results-area", classes="hidden")

            # ── Back button ──────────────────────────────────────────────
            with Center():
                yield Button("← Back to Home", id="btn-back", variant="default")
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
        error_display.update(f"[bold red]⚠ Error:[/] {message}")
        error_display.remove_class("hidden")

    def _hide_error(self) -> None:
        """Hide the error display."""
        error_display = self.query_one("#error-display", Static)
        error_display.update("")
        error_display.add_class("hidden")

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
            self._show_error("Please select a scheduling algorithm first.")
            return

        # 2. Parse process input.
        process_input = self.query_one("#process-input", TextArea)
        raw_text = process_input.text

        require_priority = algo == "priority"

        try:
            processes = parse_process_block(raw_text, require_priority=require_priority)
        except ValueError as e:
            self._show_error(str(e))
            return

        # 3. Parse quantum if Round Robin.
        quantum: int | None = None
        if algo == "rr":
            quantum_input = self.query_one("#quantum-input", Input)
            try:
                quantum = parse_quantum(quantum_input.value)
            except ValueError as e:
                self._show_error(str(e))
                return

        # 4. Run the scheduler.
        try:
            timeline = self._dispatch(algo, processes, quantum)
        except ValueError as e:
            self._show_error(f"Scheduling error: {e}")
            return

        # 5. Calculate metrics.
        metrics = calculate_metrics(processes, timeline)

        # 6. Build and display results.
        self._display_results(algo, processes, timeline, metrics)

    def _dispatch(
        self,
        algo: str,
        processes: list[SchedulerProcess],
        quantum: int | None,
    ) -> list[TimelineEntry]:
        """Dispatch to the correct scheduling function."""
        if algo == "fcfs":
            return schedule_fcfs(processes)
        elif algo == "sjf":
            return schedule_sjf(processes)
        elif algo == "rr":
            assert quantum is not None
            return schedule_round_robin(processes, quantum=quantum)
        elif algo == "priority":
            return schedule_priority(processes)
        else:
            raise ValueError(f"Unknown algorithm: {algo!r}")

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
            title="📝 Input Processes",
            show_header=True,
            header_style="bold bright_yellow",
            border_style="dim",
            expand=True,
        )
        input_table.add_column("PID", style="bold", width=8)
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

        # Compose the output.
        algo_names = dict(_ALGORITHMS)
        algo_label = algo_names.get(algo, algo)

        output = Text()
        results_area.update("")

        from rich.console import Group
        from rich.panel import Panel
        from rich.text import Text as RichText

        header_text = RichText(f"\n✅  Simulation Complete — {algo_label}\n", style="bold bright_green")
        gantt_text_renderable = RichText(gantt_text, style="bright_white")

        group = Group(
            header_text,
            input_table,
            RichText(""),
            gantt_table,
            RichText(""),
            Panel(gantt_text_renderable, title="Gantt Chart (Text)", border_style="bright_cyan"),
            RichText(""),
            metrics_table,
        )

        results_area.update(group)
        results_area.remove_class("hidden")

    def _load_example(self) -> None:
        """Load example data for the selected algorithm."""
        algo = self._get_selected_algo()
        if algo is None:
            self._show_error("Please select an algorithm first to load an example.")
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

        results_area = self.query_one("#results-area", Static)
        results_area.update("")
        results_area.add_class("hidden")

    def action_go_back(self) -> None:
        """Pop back to the home screen."""
        self.app.pop_screen()
