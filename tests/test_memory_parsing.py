"""Tests for memory input parsing helpers."""

import pytest
from sakayos.ui.parsing import parse_memory_size, parse_process_id


class TestParseMemorySize:
    def test_valid_size(self):
        assert parse_memory_size("1024") == 1024

    def test_size_with_whitespace(self):
        assert parse_memory_size("  500  ") == 500

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            parse_memory_size("")

    def test_non_integer_raises(self):
        with pytest.raises(ValueError, match="integer"):
            parse_memory_size("abc")

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="positive"):
            parse_memory_size("0")

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="positive"):
            parse_memory_size("-100")

    def test_huge_memory_size_raises(self):
        with pytest.raises(ValueError, match="Memory size.*<="):
            parse_memory_size("1000001")

    def test_custom_max_limit_can_be_disabled(self):
        assert parse_memory_size("1000001", max_size=None) == 1000001


class TestParseProcessId:
    def test_valid_pid(self):
        assert parse_process_id("P1") == "P1"

    def test_simple_pid_variants_allowed(self):
        assert parse_process_id("job_1") == "job_1"
        assert parse_process_id("process-3") == "process-3"

    def test_pid_with_whitespace(self):
        assert parse_process_id("  P2  ") == "P2"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            parse_process_id("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            parse_process_id("   ")

    def test_internal_whitespace_raises(self):
        with pytest.raises(ValueError, match="whitespace"):
            parse_process_id("job 1")

    def test_tab_whitespace_raises(self):
        with pytest.raises(ValueError, match="whitespace"):
            parse_process_id("job\t1")

    def test_comma_raises(self):
        with pytest.raises(ValueError, match="commas"):
            parse_process_id("P,1")
