"""UI rendering helpers for memory allocation."""

from __future__ import annotations

from rich.table import Table
from rich.text import Text

from sakayos.core.models import MemoryBlock


def render_memory_table(blocks: list[MemoryBlock]) -> Table:
    """Render a table showing all memory blocks."""
    table = Table(
        title="Memory Blocks",
        show_header=True,
        header_style="bold bright_blue",
        border_style="dim",
        expand=True,
    )
    table.add_column("Start Addr", justify="right", width=12)
    table.add_column("Size", justify="right", width=12)
    table.add_column("Status", style="bold", width=16)

    for block in blocks:
        status = "FREE" if block.is_free else f"Allocated: {block.process_id}"
        style = "dim bright_green" if block.is_free else "bright_yellow"
        
        table.add_row(
            str(block.start),
            str(block.size),
            Text(status, style=style),
        )

    return table


def render_memory_bar(blocks: list[MemoryBlock], total_width: int = 60) -> str:
    """Render a simple text-based visual bar of memory usage."""
    if not blocks:
        return ""

    total_size = sum(b.size for b in blocks)
    if total_size == 0:
        return ""

    bar = []
    for block in blocks:
        # Calculate proportional width, ensuring at least 1 char if size > 0
        char_count = max(1, int(round((block.size / total_size) * total_width)))
        if block.is_free:
            # Use a dotted pattern for free memory
            bar.append("░" * char_count)
        else:
            # Use block char for allocated, maybe embed PID if it fits
            fill = "█" * char_count
            bar.append(fill)

    # Note: Because of max(1, ...) the length might slightly exceed total_width,
    # but that's acceptable for a simple text visual.
    joined = "".join(bar)
    
    # We'll just return a string with a legend or the bar
    # A rich representation might be better, but text works.
    return f"[{joined}]"


def render_fragmentation_summary(
    summary: dict[str, int],
    total_size: int | None = None,
) -> Table:
    """Render compact memory usage and fragmentation metrics."""
    table = Table(
        title="Memory Summary",
        show_header=False,
        border_style="dim",
        expand=True,
    )
    table.add_column("Metric", style="bold bright_cyan")
    table.add_column("Value", justify="right")

    free_memory = summary["total_free_memory"]
    if total_size is not None:
        table.add_row("Used Memory", str(total_size - free_memory))
    table.add_row("Free Memory", str(free_memory))
    table.add_row("Largest Free Block", str(summary["largest_free_block"]))
    table.add_row("Free Blocks", str(summary["free_block_count"]))
    table.add_row("Allocated Blocks Count", str(summary["allocated_block_count"]))

    return table
