"""Textual screens for SakayOS — home, passenger, dispatch, seat allocator."""

from sakayos.screens.dispatch import DispatchScreen
from sakayos.screens.home import HomeScreen
from sakayos.screens.passenger import PassengerScreen
from sakayos.screens.seat_allocator import SeatAllocatorScreen

__all__ = [
    "HomeScreen",
    "PassengerScreen",
    "DispatchScreen",
    "SeatAllocatorScreen",
]
