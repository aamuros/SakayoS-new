"""Memory allocation algorithm simulations.

Provides a pure-logic MemoryAllocator that manages a linear address space
using contiguous blocks.  Supported placement strategies:

- First Fit  — pick the first free block large enough.
- Best Fit   — pick the smallest free block large enough.
- Worst Fit  — pick the largest free block large enough.

No OS interaction, no UI dependencies.
"""

from __future__ import annotations

from sakayos.core.models import MemoryBlock

_VALID_STRATEGIES = ("first_fit", "best_fit", "worst_fit")


class MemoryAllocator:
    """Simulated contiguous memory allocator.

    Parameters
    ----------
    total_size:
        Total number of addressable units.  Must be > 0.
    """

    # ── construction ────────────────────────────────────────────────────

    def __init__(self, total_size: int) -> None:
        if total_size <= 0:
            raise ValueError(
                f"total_size must be > 0, got {total_size}"
            )
        self._blocks: list[MemoryBlock] = [
            MemoryBlock(start=0, size=total_size, process_id=None)
        ]

    # ── public API ──────────────────────────────────────────────────────

    def allocate(self, process_id: str, size: int, strategy: str) -> bool:
        """Try to allocate *size* units for *process_id*.

        Returns True on success, False when no suitable block exists.

        Raises
        ------
        ValueError
            If *process_id* is empty, *size* <= 0, *strategy* is unknown,
            or *process_id* is already allocated.
        """
        self._validate_allocate_args(process_id, size, strategy)

        idx = self._find_block(size, strategy)
        if idx is None:
            return False

        block = self._blocks[idx]

        if block.size == size:
            # Exact match — just mark as allocated.
            self._blocks[idx] = MemoryBlock(
                start=block.start, size=block.size, process_id=process_id
            )
        else:
            # Split: allocated portion first, remainder stays free.
            allocated = MemoryBlock(
                start=block.start, size=size, process_id=process_id
            )
            remainder = MemoryBlock(
                start=block.start + size,
                size=block.size - size,
                process_id=None,
            )
            self._blocks[idx : idx + 1] = [allocated, remainder]

        return True

    def deallocate(self, process_id: str) -> bool:
        """Free the block belonging to *process_id*.

        Returns True if the process was found and freed, False otherwise.
        Adjacent free blocks are merged automatically.
        """
        idx = self._index_of_process(process_id)
        if idx is None:
            return False

        # Mark as free.
        block = self._blocks[idx]
        self._blocks[idx] = MemoryBlock(
            start=block.start, size=block.size, process_id=None
        )

        self._merge_around(idx)
        return True

    def get_blocks(self) -> list[MemoryBlock]:
        """Return a snapshot of the current block list."""
        return list(self._blocks)

    def get_fragmentation_summary(self) -> dict[str, int]:
        """Return a summary of memory fragmentation.

        Keys:
            total_free_memory     — sum of all free block sizes.
            largest_free_block    — size of the largest free block (0 if none).
            free_block_count      — number of free blocks.
            allocated_block_count — number of allocated blocks.
        """
        free_sizes: list[int] = [b.size for b in self._blocks if b.is_free]
        allocated_count = sum(1 for b in self._blocks if not b.is_free)

        return {
            "total_free_memory": sum(free_sizes),
            "largest_free_block": max(free_sizes) if free_sizes else 0,
            "free_block_count": len(free_sizes),
            "allocated_block_count": allocated_count,
        }

    # ── private helpers ─────────────────────────────────────────────────

    def _validate_allocate_args(
        self, process_id: str, size: int, strategy: str
    ) -> None:
        if not process_id:
            raise ValueError("process_id must be a non-empty string")
        if size <= 0:
            raise ValueError(f"size must be > 0, got {size}")
        if strategy not in _VALID_STRATEGIES:
            raise ValueError(
                f"strategy must be one of {_VALID_STRATEGIES}, "
                f"got '{strategy}'"
            )
        if self._index_of_process(process_id) is not None:
            raise ValueError(
                f"process_id '{process_id}' is already allocated"
            )

    def _index_of_process(self, process_id: str) -> int | None:
        """Return the index of the block belonging to *process_id*, or None."""
        for i, block in enumerate(self._blocks):
            if block.process_id == process_id:
                return i
        return None

    def _find_block(self, size: int, strategy: str) -> int | None:
        """Return the index of the chosen free block, or None."""
        candidates: list[tuple[int, MemoryBlock]] = [
            (i, b)
            for i, b in enumerate(self._blocks)
            if b.is_free and b.size >= size
        ]

        if not candidates:
            return None

        if strategy == "first_fit":
            return candidates[0][0]

        if strategy == "best_fit":
            # Smallest block that fits.
            return min(candidates, key=lambda c: c[1].size)[0]

        # strategy == "worst_fit"
        # Largest block that fits.
        return max(candidates, key=lambda c: c[1].size)[0]

    def _merge_around(self, idx: int) -> None:
        """Merge the free block at *idx* with adjacent free neighbours."""
        # Merge with right neighbour first (so idx stays valid for left merge).
        if idx + 1 < len(self._blocks) and self._blocks[idx + 1].is_free:
            right = self._blocks[idx + 1]
            merged = MemoryBlock(
                start=self._blocks[idx].start,
                size=self._blocks[idx].size + right.size,
                process_id=None,
            )
            self._blocks[idx : idx + 2] = [merged]

        # Merge with left neighbour.
        if idx - 1 >= 0 and self._blocks[idx - 1].is_free:
            left = self._blocks[idx - 1]
            merged = MemoryBlock(
                start=left.start,
                size=left.size + self._blocks[idx].size,
                process_id=None,
            )
            self._blocks[idx - 1 : idx + 1] = [merged]
