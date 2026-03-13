"""Tests for app module."""

from src.app import add, run


def test_run_returns_value():
    assert run() == "value"


def test_add_two_numbers():
    assert add(2, 3) == 5  # Will FAIL: add returns -1 (a - b)


def test_add_negative():
    assert add(-1, -2) == -3  # Will FAIL: add returns 1 (a - b)
