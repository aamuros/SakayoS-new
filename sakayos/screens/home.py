"""Home screen for SakayOS."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Static


class HomeScreen(Screen):
    """Landing screen shown when the app starts."""

    BINDINGS = [
        ("p", "open_passenger", "Passenger"),
        ("d", "open_dispatch", "Dispatch"),
        ("s", "open_seat_allocator", "Seat"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="home-container"):
            with Vertical(id="home-hero"):
                yield Label("SakayOS", id="home-title")
                yield Label(
                    "Transit Control for Operating Systems Concepts",
                    id="home-description",
                )
                yield Label(
                    "Choose a module, run a scenario, read the system state.",
                    id="home-kicker",
                )

            with Horizontal(id="home-status-strip"):
                yield Static("P  Passenger processes", classes="status-chip")
                yield Static("D  CPU dispatch", classes="status-chip")
                yield Static("S  Seat memory map", classes="status-chip")
                yield Static("Q  Quit", classes="status-chip")

            with Horizontal(id="module-list"):
                with Vertical(classes="module-card"):
                    yield Label("LINE P", classes="module-code")
                    yield Label("Passenger Manager", classes="module-title")
                    yield Label(
                        "Inspect live OS processes with sort, limit, and refresh controls.",
                        classes="module-description",
                    )
                    yield Label(
                        "OS Concept: Processes",
                        classes="module-meta module-concept",
                    )
                    yield Label(
                        "Commute Analogy: Passengers in the network",
                        classes="module-meta",
                    )
                    yield Label("Shortcut: p", classes="module-shortcut")
                    yield Button(
                        "Open Passenger Manager",
                        id="btn-passenger",
                        variant="primary",
                        compact=True,
                    )

                with Vertical(classes="module-card"):
                    yield Label("LINE D", classes="module-code")
                    yield Label("Dispatch Scheduler", classes="module-title")
                    yield Label(
                        "Run FCFS, SJF, Round Robin, and Priority scheduling scenarios.",
                        classes="module-description",
                    )
                    yield Label(
                        "OS Concept: CPU Scheduling",
                        classes="module-meta module-concept",
                    )
                    yield Label(
                        "Commute Analogy: Dispatching vehicles",
                        classes="module-meta",
                    )
                    yield Label("Shortcut: d", classes="module-shortcut")
                    yield Button(
                        "Open Dispatch Scheduler",
                        id="btn-dispatch",
                        variant="primary",
                        compact=True,
                    )

                with Vertical(classes="module-card"):
                    yield Label("LINE S", classes="module-code")
                    yield Label("Seat Allocator", classes="module-title")
                    yield Label(
                        "Allocate and free simulated memory with fit strategies.",
                        classes="module-description",
                    )
                    yield Label(
                        "OS Concept: Memory Allocation",
                        classes="module-meta module-concept",
                    )
                    yield Label(
                        "Commute Analogy: Assigning seats",
                        classes="module-meta",
                    )
                    yield Label("Shortcut: s", classes="module-shortcut")
                    yield Button(
                        "Open Seat Allocator",
                        id="btn-seat",
                        variant="primary",
                        compact=True,
                    )

            with Center():
                with Vertical(id="home-legend"):
                    yield Label("Operating Map", id="legend-title")
                    yield Static(
                        "passenger = process   vehicle = CPU   seat = memory block",
                        id="home-glossary",
                    )
            with Center():
                yield Button(
                    "Quit",
                    id="btn-quit",
                    variant="error",
                    compact=True,
                )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle navigation button clicks."""
        button_id = event.button.id
        if button_id == "btn-passenger":
            self.action_open_passenger()
        elif button_id == "btn-dispatch":
            self.action_open_dispatch()
        elif button_id == "btn-seat":
            self.action_open_seat_allocator()
        elif button_id == "btn-quit":
            self.app.exit()

    def action_open_passenger(self) -> None:
        """Open the Passenger Manager screen."""
        self.app.push_screen("passenger")

    def action_open_dispatch(self) -> None:
        """Open the Dispatch Scheduler screen."""
        self.app.push_screen("dispatch")

    def action_open_seat_allocator(self) -> None:
        """Open the Seat Allocator screen."""
        self.app.push_screen("seat_allocator")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
