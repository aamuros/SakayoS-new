"""Seat Allocator screen — placeholder.

This screen will eventually let users simulate memory allocation
strategies (First Fit, Best Fit, Worst Fit) on a virtual bus.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label


class SeatAllocatorScreen(Screen):
    """Placeholder screen for the Seat Allocator module."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="seat-container"):
            with Center():
                yield Label(
                    "💺  Seat Allocator",
                    id="screen-title",
                )
            with Center():
                yield Label(
                    "The Seat Allocator demonstrates memory allocation strategies "
                    "— First Fit, Best Fit, and Worst Fit — by simulating seats "
                    "on a bus. Allocate and deallocate blocks of seats for "
                    "passengers and observe how fragmentation changes with each "
                    "strategy. This is a pure simulation that does not touch "
                    "real system memory.",
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
