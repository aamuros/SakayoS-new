"""Memory allocation workflows shared by UI screens and tests."""

from __future__ import annotations

from dataclasses import dataclass

from sakayos.core.memory import MemoryAllocator
from sakayos.core.models import MemoryBlock
from sakayos.ui.parsing import parse_memory_size, parse_process_id


@dataclass(frozen=True)
class AllocationResult:
    """Outcome of one memory allocation attempt."""

    success: bool
    process_id: str
    size: int
    strategy: str
    blocks: list[MemoryBlock]
    summary: dict[str, int]


@dataclass(frozen=True)
class DeallocationResult:
    """Outcome of one memory deallocation attempt."""

    success: bool
    process_id: str
    blocks: list[MemoryBlock]
    summary: dict[str, int]


def initialize_memory_allocator(raw_total_size: str) -> MemoryAllocator:
    """Parse total memory size and create an allocator."""
    return MemoryAllocator(total_size=parse_memory_size(raw_total_size))


def run_memory_allocation(
    allocator: MemoryAllocator,
    raw_process_id: str,
    raw_size: str,
    strategy: str,
) -> AllocationResult:
    """Parse allocation input and allocate memory with a selected strategy."""
    process_id = parse_process_id(raw_process_id)
    size = parse_memory_size(raw_size)
    success = allocator.allocate(process_id, size, strategy)

    return AllocationResult(
        success=success,
        process_id=process_id,
        size=size,
        strategy=strategy,
        blocks=allocator.get_blocks(),
        summary=allocator.get_fragmentation_summary(),
    )


def run_memory_deallocation(
    allocator: MemoryAllocator,
    raw_process_id: str,
) -> DeallocationResult:
    """Parse deallocation input and free memory for a process."""
    process_id = parse_process_id(raw_process_id)
    success = allocator.deallocate(process_id)

    return DeallocationResult(
        success=success,
        process_id=process_id,
        blocks=allocator.get_blocks(),
        summary=allocator.get_fragmentation_summary(),
    )
