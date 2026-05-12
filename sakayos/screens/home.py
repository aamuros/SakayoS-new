"""Home screen for SakayOS.

Displays the project name, a short description, and navigation
buttons for each module: Passenger Manager, Dispatch Scheduler,
and Seat Allocator.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label


class HomeScreen(Screen):
    """Landing screen shown when the app starts."""

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="home-container"):
            with Center():
                yield Label("🚌  SakayOS", id="home-title")
            with Center():
                yield Label(
                    "A terminal-based educational dashboard that teaches "
                    "Operating Systems concepts — process management, CPU "
                    "scheduling, and memory allocation — through a Metro "
                    "Manila commuting analogy.",
                    id="home-description",
                )
            with Center():
                yield Button(
                    "🧑‍🤝‍🧑  Passenger Manager",
                    id="btn-passenger",
                    variant="primary",
                )
            with Center():
                yield Button(
                    "🚏  Dispatch Scheduler",
                    id="btn-dispatch",
                    variant="primary",
                )
            with Center():
                yield Button(
                    "💺  Seat Allocator",
                    id="btn-seat",
                    variant="primary",
                )
            with Center():
                yield Button(
                    "❌  Quit",
                    id="btn-quit",
                    variant="error",
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
