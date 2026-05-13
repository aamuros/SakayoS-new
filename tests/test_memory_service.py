"""Tests for memory service workflows independent of Textual."""

from __future__ import annotations

import pytest

from sakayos.core.memory import MemoryAllocator
from sakayos.services.memory_service import (
    AllocationResult,
    DeallocationResult,
    initialize_memory_allocator,
    run_memory_allocation,
    run_memory_deallocation,
)


class TestMemoryService:
    def test_initialize_memory_allocator_parses_size(self) -> None:
        allocator = initialize_memory_allocator("256")

        assert isinstance(allocator, MemoryAllocator)
        assert allocator.total_size == 256

    def test_allocation_returns_structured_result(self) -> None:
        allocator = initialize_memory_allocator("256")
        result = run_memory_allocation(
            allocator,
            " P1 ",
            "100",
            "first_fit",
        )

        assert isinstance(result, AllocationResult)
        assert result.success is True
        assert result.process_id == "P1"
        assert result.size == 100
        assert result.strategy == "first_fit"
        assert result.blocks[0].process_id == "P1"
        assert result.summary["total_free_memory"] == 156

    def test_failed_allocation_returns_failure_result(self) -> None:
        allocator = initialize_memory_allocator("128")
        result = run_memory_allocation(
            allocator,
            "P1",
            "256",
            "first_fit",
        )

        assert result.success is False
        assert result.process_id == "P1"
        assert result.size == 256
        assert result.summary["total_free_memory"] == 128

    def test_deallocation_returns_structured_result(self) -> None:
        allocator = initialize_memory_allocator("256")
        run_memory_allocation(allocator, "P1", "100", "first_fit")
        result = run_memory_deallocation(allocator, "P1")

        assert isinstance(result, DeallocationResult)
        assert result.success is True
        assert result.process_id == "P1"
        assert len(result.blocks) == 1
        assert result.summary["total_free_memory"] == 256

    def test_missing_deallocation_returns_failure_result(self) -> None:
        allocator = initialize_memory_allocator("256")
        result = run_memory_deallocation(allocator, "P1")

        assert result.success is False
        assert result.process_id == "P1"

    def test_parse_errors_are_raised_before_allocator_call(self) -> None:
        allocator = initialize_memory_allocator("256")

        with pytest.raises(ValueError, match="Process ID"):
            run_memory_allocation(allocator, " ", "100", "first_fit")
