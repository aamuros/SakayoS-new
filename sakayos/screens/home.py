"""Home screen for SakayOS.

Displays the project name, a short description, and navigation
buttons for each module: Passenger Manager, Dispatch Scheduler,
and Seat Allocator.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Static


class HomeScreen(Screen):
    """Landing screen shown when the app starts."""

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="home-container"):
            with Center():
                yield Label("SakayOS", id="home-title")
            with Center():
                yield Label(
                    "A small operating systems lab with commuting-inspired modules.",
                    id="home-description",
                )

            with Vertical(id="module-list"):
                with Vertical(classes="module-card"):
                    yield Label("Passenger Manager", classes="module-title")
                    yield Label(
                        "View running OS processes.",
                        classes="module-description",
                    )
                    yield Button(
                        "Open",
                        id="btn-passenger",
                        variant="primary",
                        compact=True,
                    )

                with Vertical(classes="module-card"):
                    yield Label("Dispatch Scheduler", classes="module-title")
                    yield Label(
                        "Simulate CPU scheduling.",
                        classes="module-description",
                    )
                    yield Button(
                        "Open",
                        id="btn-dispatch",
                        variant="primary",
                        compact=True,
                    )

                with Vertical(classes="module-card"):
                    yield Label("Seat Allocator", classes="module-title")
                    yield Label(
                        "Simulate memory allocation.",
                        classes="module-description",
                    )
                    yield Button(
                        "Open",
                        id="btn-seat",
                        variant="primary",
                        compact=True,
                    )

            with Center():
                yield Static(
                    "[dim]Glossary: passenger = process, vehicle = CPU, seat = memory block[/]",
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
            self.app.push_screen("passenger")
        elif button_id == "btn-dispatch":
            self.app.push_screen("dispatch")
        elif button_id == "btn-seat":
            self.app.push_screen("seat_allocator")
        elif button_id == "btn-quit":
            self.app.exit()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
