"""Tests for the SakayOS Textual application skeleton.

Covers:
- App object creation and importability.
- Screen registration.
- Screen class importability.
- Basic attributes (title, CSS path).

Deliberately minimal — avoids testing visual layout per Phase 6 guidelines.
"""

from __future__ import annotations

from pathlib import Path

from sakayos.app import SakayOSApp, main
from sakayos.screens import (
    DispatchScreen,
    HomeScreen,
    PassengerScreen,
    SeatAllocatorScreen,
)


# ── Import / creation tests ────────────────────────────────────────────────


class TestAppCreation:
    """Verify the SakayOSApp class can be imported and instantiated."""

    def test_app_class_importable(self) -> None:
        """SakayOSApp should be importable from sakayos.app."""
        assert SakayOSApp is not None

    def test_app_instantiation(self) -> None:
        """SakayOSApp() should create an app instance without errors."""
        app = SakayOSApp()
        assert app is not None

    def test_main_function_exists(self) -> None:
        """The main() entry point should be callable."""
        assert callable(main)


# ── App attribute tests ────────────────────────────────────────────────────


class TestAppAttributes:
    """Verify key configuration attributes on the app."""

    def test_app_title(self) -> None:
        """App title should be 'SakayOS'."""
        app = SakayOSApp()
        assert app.TITLE == "SakayOS"

    def test_app_sub_title(self) -> None:
        """App sub-title should be set."""
        app = SakayOSApp()
        assert app.SUB_TITLE == "OS Concepts Dashboard"

    def test_css_path_exists(self) -> None:
        """The CSS file referenced by the app should exist on disk."""
        css_path = Path(SakayOSApp.CSS_PATH)
        assert css_path.exists(), f"CSS file not found at {css_path}"


# ── Screen registration tests ──────────────────────────────────────────────


class TestScreenRegistration:
    """Verify the app registers the expected named screens."""

    def test_screens_dict_has_home(self) -> None:
        assert "home" in SakayOSApp.SCREENS

    def test_screens_dict_has_passenger(self) -> None:
        assert "passenger" in SakayOSApp.SCREENS

    def test_screens_dict_has_dispatch(self) -> None:
        assert "dispatch" in SakayOSApp.SCREENS

    def test_screens_dict_has_seat_allocator(self) -> None:
        assert "seat_allocator" in SakayOSApp.SCREENS

    def test_screens_count(self) -> None:
        """There should be exactly four registered screens."""
        assert len(SakayOSApp.SCREENS) == 4


# ── Screen class import tests ──────────────────────────────────────────────


class TestScreenImports:
    """Verify that each screen class is importable and is a Screen subclass."""

    def test_home_screen_importable(self) -> None:
        assert HomeScreen is not None

    def test_passenger_screen_importable(self) -> None:
        assert PassengerScreen is not None

    def test_dispatch_screen_importable(self) -> None:
        assert DispatchScreen is not None

    def test_seat_allocator_screen_importable(self) -> None:
        assert SeatAllocatorScreen is not None

    def test_all_screens_are_screen_subclasses(self) -> None:
        from textual.screen import Screen

        for screen_cls in (
            HomeScreen,
            PassengerScreen,
            DispatchScreen,
            SeatAllocatorScreen,
        ):
            assert issubclass(screen_cls, Screen), (
                f"{screen_cls.__name__} is not a Screen subclass"
            )
