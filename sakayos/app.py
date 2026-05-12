"""SakayOS — Main application entry point.

A Textual-based terminal dashboard for exploring OS concepts
through Metro Manila commuting analogies.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import App

from sakayos.screens.dispatch import DispatchScreen
from sakayos.screens.home import HomeScreen
from sakayos.screens.passenger import PassengerScreen
from sakayos.screens.seat_allocator import SeatAllocatorScreen

# Path to the Textual CSS file (lives alongside this module).
CSS_PATH = Path(__file__).parent / "app.tcss"


class SakayOSApp(App):
    """The main SakayOS Textual application."""

    TITLE = "SakayOS"
    SUB_TITLE = "OS Concepts Dashboard"
    CSS_PATH = CSS_PATH

    SCREENS = {
        "home": HomeScreen,
        "passenger": PassengerScreen,
        "dispatch": DispatchScreen,
        "seat_allocator": SeatAllocatorScreen,
    }

    def on_mount(self) -> None:
        """Push the home screen on startup."""
        self.push_screen("home")


def main() -> None:
    """Launch the SakayOS application."""
    app = SakayOSApp()
    app.run()


if __name__ == "__main__":
    main()
