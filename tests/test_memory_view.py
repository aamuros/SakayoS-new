"""Tests for sakayos.ui.memory_view."""

import pytest
from rich.table import Table

from sakayos.core.models import MemoryBlock
from sakayos.ui.memory_view import render_memory_table, render_memory_bar, render_fragmentation_summary


def test_render_memory_table_empty():
    blocks = []
    table = render_memory_table(blocks)
    assert isinstance(table, Table)
    # Just asserting it returns a table without crashing


def test_render_memory_table_with_blocks():
    blocks = [
        MemoryBlock(start=0, size=100, process_id="P1"),
        MemoryBlock(start=100, size=50, process_id=None),
    ]
    table = render_memory_table(blocks)
    assert isinstance(table, Table)
    # The table should have columns for Start, Size, Status (Process ID / Free)


def test_render_memory_bar():
    blocks = [
        MemoryBlock(start=0, size=100, process_id="P1"),
        MemoryBlock(start=100, size=50, process_id=None),
    ]
    text = render_memory_bar(blocks, total_width=50)
    assert isinstance(text, str)
    assert "░" in text or " " in text
    assert "█" in text


def test_render_fragmentation_summary():
    summary_data = {
        "total_free_memory": 150,
        "largest_free_block": 100,
        "free_block_count": 2,
        "allocated_block_count": 3,
    }
    table = render_fragmentation_summary(summary_data)
    assert isinstance(table, Table)
