"""Pytest configuration for loading environment variables."""

from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load .env file at module import time (before pytest collection)
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Ensure environment variables are loaded from .env file."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)


@pytest.fixture(scope="session")
def gpu_available() -> bool:
    """Check if GPU (CUDA) is available for testing.

    Returns:
        bool: True if CUDA GPU is available, False otherwise.
    """
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False
