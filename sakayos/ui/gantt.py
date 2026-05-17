"""Gantt chart rendering utilities for scheduling timelines.

Converts a list[TimelineEntry] into readable text representations:
- render_gantt_text():  plain-text Gantt bar + legend (deterministic, testable)
- render_gantt_table(): Rich Table for display in Textual UIs
"""

from __future__ import annotations

from rich import box
from rich.table import Table
from rich.text import Text

from sakayos.core.models import TimelineEntry


# ── Color palette for processes ─────────────────────────────────────────────

_COLORS = [
    "#2dd4bf",
    "#f59e0b",
    "#22c55e",
    "#7dd3fc",
    "#fb7185",
    "#a78bfa",
    "#f472b6",
    "#f97316",
]


def _pid_color(pid: str, pid_list: list[str]) -> str:
    """Return a consistent color for a given pid."""
    try:
        idx = pid_list.index(pid)
    except ValueError:
        idx = 0
    return _COLORS[idx % len(_COLORS)]


# ── Plain-text Gantt (deterministic, for testing) ───────────────────────────


def render_gantt_text(timeline: list[TimelineEntry]) -> str:
    """Render a plain-text Gantt chart from a scheduling timeline.

    Output format (example):
        Time  0    2    4    5    7    8    9
              |P1  |P2  |P3 |P1  |P2 |P1 |
        ──────────────────────────────────────

        P1: [0-2] [5-7] [8-9]
        P2: [2-4] [7-8]
        P3: [4-5]

    Returns an empty string for an empty timeline.
    """
    if not timeline:
        return ""

    # ── Build the Gantt bar ──────────────────────────────────────────────

    # Collect all unique time markers (starts and ends).
    time_points: list[int] = []
    for entry in timeline:
        if entry.start not in time_points:
            time_points.append(entry.start)
        if entry.end not in time_points:
            time_points.append(entry.end)
    time_points.sort()

    # Build header row (time markers) and bar row (process labels).
    # Each column is sized to fit the widest label within that span.
    col_width = 4  # minimum column width

    header_parts: list[str] = []
    bar_parts: list[str] = []

    for i, tp in enumerate(time_points):
        tp_str = str(tp)
        if i < len(time_points) - 1:
            # Find which timeline entry covers this span.
            span_start = tp
            span_end = time_points[i + 1]
            label = ""
            for entry in timeline:
                if entry.start <= span_start and entry.end >= span_end:
                    label = entry.pid
                    break

            # Detect idle gap (no entry covers this span).
            if not label:
                label = "IDLE"

            width = max(col_width, len(label) + 1, len(tp_str) + 1)
            header_parts.append(tp_str.ljust(width))
            bar_parts.append(("|" + label).ljust(width))
        else:
            # Last time point — just the number and closing pipe.
            header_parts.append(tp_str)
            bar_parts.append("|")

    header_line = "".join(header_parts)
    bar_line = "".join(bar_parts)
    separator = "─" * len(bar_line)

    # ── Build per-process legend ─────────────────────────────────────────

    # Collect spans grouped by pid, preserving first-appearance order.
    pid_order: list[str] = []
    pid_spans: dict[str, list[str]] = {}
    for entry in timeline:
        span_str = f"[{entry.start}-{entry.end}]"
        if entry.pid not in pid_spans:
            pid_order.append(entry.pid)
            pid_spans[entry.pid] = []
        pid_spans[entry.pid].append(span_str)

    legend_lines = [f"{pid}: {' '.join(pid_spans[pid])}" for pid in pid_order]

    # ── Assemble ─────────────────────────────────────────────────────────

    lines = [
        f"Time  {header_line}",
        f"      {bar_line}",
        f"      {separator}",
        "",
    ]
    lines.extend(legend_lines)
    return "\n".join(lines)


# ── Rich Table Gantt (for Textual UI display) ───────────────────────────────


def render_gantt_table(timeline: list[TimelineEntry]) -> Table:
    """Render a Rich Table representation of the Gantt timeline.

    Each row is a timeline entry with pid, start, end, and duration.
    """
    table = Table(
        title="Schedule Timeline",
        show_header=True,
        header_style="bold #7dd3fc",
        border_style="#334155",
        box=box.SIMPLE,
        row_styles=["", "#94a3b8"],
        expand=True,
    )
    table.add_column("#", style="#64748b", width=4, justify="right")
    table.add_column("PID", style="bold", width=8)
    table.add_column("Start", justify="right", width=8)
    table.add_column("End", justify="right", width=8)
    table.add_column("Duration", justify="right", width=10)

    # Determine unique pids for coloring.
    pid_list: list[str] = []
    for entry in timeline:
        if entry.pid not in pid_list:
            pid_list.append(entry.pid)

    for i, entry in enumerate(timeline, 1):
        color = _pid_color(entry.pid, pid_list)
        table.add_row(
            str(i),
            Text(entry.pid, style=color),
            str(entry.start),
            str(entry.end),
            str(entry.duration),
        )

    return table


# ── Metrics Table ───────────────────────────────────────────────────────────


def render_metrics_table(
    metrics: dict[str, dict[str, float]],
    pid_order: list[str] | None = None,
) -> Table:
    """Render a Rich Table of per-process scheduling metrics.

    Args:
        metrics:   dict mapping pid → {completion_time, turnaround_time, waiting_time}.
        pid_order: optional ordering; defaults to sorted pids.
    """
    table = Table(
        title="Detailed Metrics",
        show_header=True,
        header_style="bold #22c55e",
        border_style="#334155",
        box=box.SIMPLE,
        row_styles=["", "#94a3b8"],
        expand=True,
    )
    table.add_column("PID", style="bold #2dd4bf", width=8)
    table.add_column("Completion", justify="right", width=12)
    table.add_column("Turnaround", justify="right", width=12)
    table.add_column("Waiting", justify="right", width=12)

    ordered = pid_order if pid_order else sorted(metrics.keys())

    total_tat = 0.0
    total_wt = 0.0
    count = 0

    for pid in ordered:
        m = metrics[pid]
        ct = m["completion_time"]
        tat = m["turnaround_time"]
        wt = m["waiting_time"]
        total_tat += tat
        total_wt += wt
        count += 1
        table.add_row(pid, str(int(ct)), str(int(tat)), str(int(wt)))

    # Add averages row.
    if count > 0:
        avg_tat = total_tat / count
        avg_wt = total_wt / count
        table.add_row(
            Text("AVG", style="bold italic"),
            "—",
            f"{avg_tat:.2f}",
            f"{avg_wt:.2f}",
            style="dim",
        )

    return table
