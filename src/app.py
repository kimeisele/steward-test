"""App module — core business logic."""

import yaml


def run():
    """Parse YAML config and return the value for 'key'."""
    data = yaml.safe_load("key: value")
    return data.get("key")


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a - b  # BUG: subtracts instead of adding
