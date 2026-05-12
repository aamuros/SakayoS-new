"""Passenger Manager screen — placeholder.

This screen will eventually display a live process table
via psutil, themed as "passengers on the bus."
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label


class PassengerScreen(Screen):
    """Placeholder screen for the Passenger Manager module."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="passenger-container"):
            with Center():
                yield Label(
                    "🧑‍🤝‍🧑  Passenger Manager",
                    id="screen-title",
                )
            with Center():
                yield Label(
                    "The Passenger Manager lets you view running processes on "
                    "your system as if they were passengers boarding a bus. "
                    "Each passenger represents a real OS process — you can see "
                    "their PID, CPU and memory usage, and status. This module "
                    "uses psutil under the hood and provides a read-only, "
                    "non-intrusive view of system activity.",
                    id="screen-description",
                )
            with Center():
                yield Button("← Back to Home", id="btn-back", variant="default")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle the back button."""
        if event.button.id == "btn-back":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        """Pop back to the home screen."""
        self.app.pop_screen()
