"""App module with undeclared dependency and broken import."""

import yaml  # undeclared in pyproject.toml
from src.utils import helper  # broken: utils.py doesn't exist


def run():
    data = yaml.safe_load("key: value")
    return helper(data)
