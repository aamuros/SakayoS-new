"""Tests for sakayos.core.memory — written BEFORE implementation (TDD)."""

import pytest

from sakayos.core.models import MemoryBlock
from sakayos.core.memory import MemoryAllocator


def assert_memory_invariants(alloc: MemoryAllocator) -> None:
    blocks = alloc.get_blocks()
    assert sum(block.size for block in blocks) == alloc.total_size

    expected_start = 0
    allocated_process_ids: set[str] = set()

    for index, block in enumerate(blocks):
        assert block.size > 0
        assert block.start == expected_start
        if index > 0:
            assert not (blocks[index - 1].is_free and block.is_free)
        if block.process_id is not None:
            assert block.process_id not in allocated_process_ids
            allocated_process_ids.add(block.process_id)
        expected_start += block.size


# ── 1. Initial State ───────────────────────────────────────────────────────


class TestInitialState:
    """Memory starts as one free block from address 0 with size total_size."""

    def test_initial_memory_has_one_free_block(self):
        alloc = MemoryAllocator(total_size=1024)
        blocks = alloc.get_blocks()
        assert len(blocks) == 1
        assert blocks[0].start == 0
        assert blocks[0].size == 1024
        assert blocks[0].is_free is True

    def test_initial_memory_different_size(self):
        alloc = MemoryAllocator(total_size=256)
        blocks = alloc.get_blocks()
        assert len(blocks) == 1
        assert blocks[0].size == 256

    def test_total_size_is_readable(self):
        alloc = MemoryAllocator(total_size=512)
        assert alloc.total_size == 512


# ── 2. First Fit ───────────────────────────────────────────────────────────


class TestFirstFit:
    """First Fit chooses the first free block large enough."""

    def test_first_fit_allocates_into_first_suitable_block(self):
        alloc = MemoryAllocator(total_size=1024)
        assert alloc.allocate("P1", 256, "first_fit") is True
        blocks = alloc.get_blocks()
        # Two blocks: [P1: 0-255] [free: 256-1023]
        assert len(blocks) == 2
        assert blocks[0].process_id == "P1"
        assert blocks[0].start == 0
        assert blocks[0].size == 256
        assert blocks[1].is_free is True
        assert blocks[1].start == 256
        assert blocks[1].size == 768

    def test_first_fit_chooses_first_of_multiple_suitable(self):
        """Given free blocks of [100, 200, 300], FF picks the 100-block if >= requested."""
        alloc = MemoryAllocator(total_size=600)
        # Fill then free to create a specific layout:
        # [P1:100][P2:200][P3:300]
        alloc.allocate("P1", 100, "first_fit")
        alloc.allocate("P2", 200, "first_fit")
        alloc.allocate("P3", 300, "first_fit")
        # Free P1 and P3 → free blocks at start (100) and end (300)
        alloc.deallocate("P1")
        alloc.deallocate("P3")
        # Layout: [free:100][P2:200][free:300]
        # Request 50 — first fit should use the first free block at address 0
        alloc.allocate("P4", 50, "first_fit")
        blocks = alloc.get_blocks()
        # [P4:50][free:50][P2:200][free:300]
        assert blocks[0].process_id == "P4"
        assert blocks[0].start == 0
        assert blocks[0].size == 50

    def test_first_fit_exact_match_no_split(self):
        alloc = MemoryAllocator(total_size=256)
        assert alloc.allocate("P1", 256, "first_fit") is True
        blocks = alloc.get_blocks()
        assert len(blocks) == 1
        assert blocks[0].process_id == "P1"
        assert blocks[0].size == 256


# ── 3. Best Fit ────────────────────────────────────────────────────────────


class TestBestFit:
    """Best Fit chooses the smallest free block large enough."""

    def test_best_fit_chooses_smallest_suitable_free_block(self):
        alloc = MemoryAllocator(total_size=600)
        # Create layout: [free:100][P2:200][free:300]
        alloc.allocate("P1", 100, "first_fit")
        alloc.allocate("P2", 200, "first_fit")
        alloc.allocate("P3", 300, "first_fit")
        alloc.deallocate("P1")
        alloc.deallocate("P3")
        # Layout: [free:100][P2:200][free:300]
        # Request 80 — best fit should choose the 100-sized block (smallest that fits)
        alloc.allocate("P4", 80, "best_fit")
        blocks = alloc.get_blocks()
        # [P4:80][free:20][P2:200][free:300]
        assert blocks[0].process_id == "P4"
        assert blocks[0].start == 0
        assert blocks[0].size == 80

    def test_best_fit_exact_match_preferred(self):
        alloc = MemoryAllocator(total_size=600)
        alloc.allocate("P1", 100, "first_fit")
        alloc.allocate("P2", 200, "first_fit")
        alloc.allocate("P3", 300, "first_fit")
        alloc.deallocate("P1")
        alloc.deallocate("P3")
        # Layout: [free:100][P2:200][free:300]
        # Request exactly 100 — best fit picks the 100-block (exact match)
        alloc.allocate("P4", 100, "best_fit")
        blocks = alloc.get_blocks()
        assert blocks[0].process_id == "P4"
        assert blocks[0].size == 100


# ── 4. Worst Fit ───────────────────────────────────────────────────────────


class TestWorstFit:
    """Worst Fit chooses the largest free block large enough."""

    def test_worst_fit_chooses_largest_suitable_free_block(self):
        alloc = MemoryAllocator(total_size=600)
        # Create layout: [free:100][P2:200][free:300]
        alloc.allocate("P1", 100, "first_fit")
        alloc.allocate("P2", 200, "first_fit")
        alloc.allocate("P3", 300, "first_fit")
        alloc.deallocate("P1")
        alloc.deallocate("P3")
        # Layout: [free:100][P2:200][free:300]
        # Request 80 — worst fit should pick the 300-sized block (largest)
        alloc.allocate("P4", 80, "worst_fit")
        blocks = alloc.get_blocks()
        # [free:100][P2:200][P4:80][free:220]
        p4_block = [b for b in blocks if b.process_id == "P4"][0]
        assert p4_block.start == 300  # starts where the 300-block was
        assert p4_block.size == 80

    def test_worst_fit_large_remainder(self):
        alloc = MemoryAllocator(total_size=1024)
        alloc.allocate("P1", 10, "worst_fit")
        blocks = alloc.get_blocks()
        assert blocks[0].process_id == "P1"
        assert blocks[0].size == 10
        assert blocks[1].is_free is True
        assert blocks[1].size == 1014


# ── 5. Allocation Failure ──────────────────────────────────────────────────


class TestAllocationFailure:
    """Allocation fails when no block is large enough."""

    def test_allocation_fails_when_no_block_large_enough(self):
        alloc = MemoryAllocator(total_size=100)
        assert alloc.allocate("P1", 101, "first_fit") is False

    def test_allocation_fails_after_memory_exhausted(self):
        alloc = MemoryAllocator(total_size=100)
        alloc.allocate("P1", 60, "first_fit")
        alloc.allocate("P2", 40, "first_fit")
        assert alloc.allocate("P3", 1, "first_fit") is False

    def test_allocation_fails_fragmented_memory(self):
        """Total free memory is enough but no single block is large enough."""
        alloc = MemoryAllocator(total_size=300)
        # [P1:100][P2:100][P3:100]
        alloc.allocate("P1", 100, "first_fit")
        alloc.allocate("P2", 100, "first_fit")
        alloc.allocate("P3", 100, "first_fit")
        # Free P1 and P3 → [free:100][P2:100][free:100] = 200 free, but max block = 100
        alloc.deallocate("P1")
        alloc.deallocate("P3")
        assert alloc.allocate("P4", 150, "best_fit") is False


# ── 6. Deallocation ────────────────────────────────────────────────────────


class TestDeallocation:
    """Deallocation frees a block."""

    def test_deallocation_frees_a_block(self):
        alloc = MemoryAllocator(total_size=256)
        alloc.allocate("P1", 100, "first_fit")
        assert alloc.deallocate("P1") is True
        blocks = alloc.get_blocks()
        # Should be back to one free block after merge
        assert len(blocks) == 1
        assert blocks[0].is_free is True
        assert blocks[0].size == 256

    def test_deallocation_returns_false_for_unknown_process(self):
        alloc = MemoryAllocator(total_size=256)
        assert alloc.deallocate("nonexistent") is False

    def test_repeated_deallocation_attempts_return_false_after_first_free(self):
        alloc = MemoryAllocator(total_size=256)
        alloc.allocate("P1", 100, "first_fit")

        assert alloc.deallocate("P1") is True
        assert alloc.deallocate("P1") is False
        assert alloc.deallocate("P1") is False

        blocks = alloc.get_blocks()
        assert len(blocks) == 1
        assert blocks[0].is_free is True
        assert blocks[0].size == 256
        assert_memory_invariants(alloc)

    def test_deallocation_preserves_other_allocations(self):
        alloc = MemoryAllocator(total_size=300)
        alloc.allocate("P1", 100, "first_fit")
        alloc.allocate("P2", 100, "first_fit")
        alloc.allocate("P3", 100, "first_fit")
        alloc.deallocate("P2")
        blocks = alloc.get_blocks()
        # [P1:100][free:100][P3:100]
        assert len(blocks) == 3
        assert blocks[0].process_id == "P1"
        assert blocks[1].is_free is True
        assert blocks[1].size == 100
        assert blocks[2].process_id == "P3"


# ── 7. Merging Adjacent Free Blocks ───────────────────────────────────────


class TestMerging:
    """Adjacent free blocks merge after deallocation."""

    def test_merge_with_right_neighbor(self):
        alloc = MemoryAllocator(total_size=300)
        alloc.allocate("P1", 100, "first_fit")
        alloc.allocate("P2", 100, "first_fit")
        # [P1:100][P2:100][free:100]
        alloc.deallocate("P2")
        # P2 freed → should merge with trailing free → [P1:100][free:200]
        blocks = alloc.get_blocks()
        assert len(blocks) == 2
        assert blocks[1].is_free is True
        assert blocks[1].size == 200

    def test_merge_with_left_neighbor(self):
        alloc = MemoryAllocator(total_size=300)
        alloc.allocate("P1", 100, "first_fit")
        alloc.allocate("P2", 100, "first_fit")
        alloc.allocate("P3", 100, "first_fit")
        # [P1:100][P2:100][P3:100]
        alloc.deallocate("P1")
        # [free:100][P2:100][P3:100]
        alloc.deallocate("P2")
        # free:100 merges with freed P2 → [free:200][P3:100]
        blocks = alloc.get_blocks()
        assert len(blocks) == 2
        assert blocks[0].is_free is True
        assert blocks[0].size == 200
        assert blocks[0].start == 0

    def test_merge_with_both_neighbors(self):
        alloc = MemoryAllocator(total_size=300)
        alloc.allocate("P1", 100, "first_fit")
        alloc.allocate("P2", 100, "first_fit")
        alloc.allocate("P3", 100, "first_fit")
        # [P1:100][P2:100][P3:100]
        alloc.deallocate("P1")
        alloc.deallocate("P3")
        # [free:100][P2:100][free:100]
        alloc.deallocate("P2")
        # All merge → [free:300]
        blocks = alloc.get_blocks()
        assert len(blocks) == 1
        assert blocks[0].is_free is True
        assert blocks[0].size == 300
        assert blocks[0].start == 0

    def test_allocation_after_fragmentation_and_merge_recovery(self):
        alloc = MemoryAllocator(total_size=500)
        alloc.allocate("P1", 100, "first_fit")
        alloc.allocate("P2", 150, "first_fit")
        alloc.allocate("P3", 100, "first_fit")
        alloc.allocate("P4", 150, "first_fit")

        alloc.deallocate("P2")
        alloc.deallocate("P4")
        assert alloc.allocate("P5", 250, "best_fit") is False

        alloc.deallocate("P3")
        assert alloc.allocate("P5", 250, "best_fit") is True

        p5_block = [b for b in alloc.get_blocks() if b.process_id == "P5"][0]
        assert p5_block.start == 100
        assert p5_block.size == 250
        assert_memory_invariants(alloc)


# ── 8. Duplicate Process ID ───────────────────────────────────────────────


class TestDuplicateProcessId:
    """Duplicate process_id allocation raises ValueError."""

    def test_duplicate_process_id_raises_valueerror(self):
        alloc = MemoryAllocator(total_size=256)
        alloc.allocate("P1", 50, "first_fit")
        with pytest.raises(ValueError, match="P1"):
            alloc.allocate("P1", 50, "first_fit")


# ── 9. Input Validation ───────────────────────────────────────────────────


class TestInputValidation:
    """Invalid size, process_id, total_size, and strategy raise ValueError."""

    def test_invalid_total_size_zero(self):
        with pytest.raises(ValueError, match="total_size"):
            MemoryAllocator(total_size=0)

    def test_invalid_total_size_negative(self):
        with pytest.raises(ValueError, match="total_size"):
            MemoryAllocator(total_size=-10)

    def test_invalid_process_id_empty_string(self):
        alloc = MemoryAllocator(total_size=256)
        with pytest.raises(ValueError, match="process_id"):
            alloc.allocate("", 50, "first_fit")

    def test_invalid_size_zero(self):
        alloc = MemoryAllocator(total_size=256)
        with pytest.raises(ValueError, match="size"):
            alloc.allocate("P1", 0, "first_fit")

    def test_invalid_size_negative(self):
        alloc = MemoryAllocator(total_size=256)
        with pytest.raises(ValueError, match="size"):
            alloc.allocate("P1", -10, "first_fit")

    def test_invalid_strategy(self):
        alloc = MemoryAllocator(total_size=256)
        with pytest.raises(ValueError, match="strategy"):
            alloc.allocate("P1", 50, "random_fit")


# ── 10. Fragmentation Summary ─────────────────────────────────────────────


class TestFragmentationSummary:
    """Fragmentation summary is correct after multiple allocations/deallocations."""

    def test_initial_fragmentation_summary(self):
        alloc = MemoryAllocator(total_size=1024)
        summary = alloc.get_fragmentation_summary()
        assert summary["total_free_memory"] == 1024
        assert summary["largest_free_block"] == 1024
        assert summary["free_block_count"] == 1
        assert summary["allocated_block_count"] == 0

    def test_fragmentation_after_allocations(self):
        alloc = MemoryAllocator(total_size=1024)
        alloc.allocate("P1", 200, "first_fit")
        alloc.allocate("P2", 300, "first_fit")
        summary = alloc.get_fragmentation_summary()
        assert summary["total_free_memory"] == 524
        assert summary["largest_free_block"] == 524
        assert summary["free_block_count"] == 1
        assert summary["allocated_block_count"] == 2

    def test_fragmentation_after_deallocation_creates_fragments(self):
        alloc = MemoryAllocator(total_size=300)
        alloc.allocate("P1", 100, "first_fit")
        alloc.allocate("P2", 100, "first_fit")
        alloc.allocate("P3", 100, "first_fit")
        alloc.deallocate("P1")
        alloc.deallocate("P3")
        # [free:100][P2:100][free:100]
        summary = alloc.get_fragmentation_summary()
        assert summary["total_free_memory"] == 200
        assert summary["largest_free_block"] == 100
        assert summary["free_block_count"] == 2
        assert summary["allocated_block_count"] == 1

    def test_fragmentation_fully_allocated(self):
        alloc = MemoryAllocator(total_size=100)
        alloc.allocate("P1", 100, "first_fit")
        summary = alloc.get_fragmentation_summary()
        assert summary["total_free_memory"] == 0
        assert summary["largest_free_block"] == 0
        assert summary["free_block_count"] == 0
        assert summary["allocated_block_count"] == 1


# ── 11. Invariants ─────────────────────────────────────────────────────────


class TestMemoryInvariants:
    """Allocator operations preserve internal block-list invariants."""

    @pytest.mark.parametrize("strategy", ["first_fit", "best_fit", "worst_fit"])
    def test_long_allocation_deallocation_sequence_preserves_invariants(
        self, strategy: str
    ):
        alloc = MemoryAllocator(total_size=1000)
        operations = [
            ("alloc", "P1", 120),
            ("alloc", "P2", 80),
            ("alloc", "P3", 200),
            ("alloc", "P4", 50),
            ("alloc", "P5", 75),
            ("alloc", "P6", 125),
            ("free", "P2", None),
            ("free", "P4", None),
            ("alloc", "P7", 45),
            ("alloc", "P8", 70),
            ("free", "P1", None),
            ("free", "P3", None),
            ("alloc", "P9", 250),
            ("free", "P5", None),
            ("free", "P7", None),
            ("alloc", "P10", 60),
            ("free", "P6", None),
            ("free", "P8", None),
            ("alloc", "P11", 180),
        ]

        for action, process_id, size in operations:
            if action == "alloc":
                assert size is not None
                alloc.allocate(process_id, size, strategy)
            else:
                alloc.deallocate(process_id)
            assert_memory_invariants(alloc)

    def test_get_blocks_returns_snapshot_objects(self):
        alloc = MemoryAllocator(total_size=100)
        blocks = alloc.get_blocks()
        blocks[0].size = 1

        assert alloc.get_blocks()[0].size == 100
        assert_memory_invariants(alloc)

    def test_internal_validation_catches_total_size_mismatch(self):
        alloc = MemoryAllocator(total_size=100)
        alloc._blocks = [MemoryBlock(start=0, size=99, process_id=None)]

        with pytest.raises(RuntimeError, match="block sizes sum"):
            alloc._validate_invariants()

    def test_internal_validation_catches_non_contiguous_blocks(self):
        alloc = MemoryAllocator(total_size=100)
        alloc._blocks = [
            MemoryBlock(start=0, size=50, process_id="P1"),
            MemoryBlock(start=60, size=40, process_id=None),
        ]

        with pytest.raises(RuntimeError, match="starts at 60"):
            alloc._validate_invariants()

    def test_internal_validation_catches_invalid_block_size(self):
        alloc = MemoryAllocator(total_size=100)
        alloc._blocks[0].size = 0

        with pytest.raises(RuntimeError, match="invalid size"):
            alloc._validate_invariants()

    def test_internal_validation_catches_duplicate_allocated_process_ids(self):
        alloc = MemoryAllocator(total_size=100)
        alloc._blocks = [
            MemoryBlock(start=0, size=40, process_id="P1"),
            MemoryBlock(start=40, size=60, process_id="P1"),
        ]

        with pytest.raises(RuntimeError, match="duplicate allocated process_id"):
            alloc._validate_invariants()

    def test_internal_validation_catches_unmerged_adjacent_free_blocks(self):
        alloc = MemoryAllocator(total_size=100)
        alloc._blocks = [
            MemoryBlock(start=0, size=40, process_id=None),
            MemoryBlock(start=40, size=60, process_id=None),
        ]

        with pytest.raises(RuntimeError, match="adjacent free blocks"):
            alloc._validate_invariants()
