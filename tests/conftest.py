"""Pytest configuration and fixtures"""
import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def sample_urdf():
    """Path to sample URDF file"""
    return Path(__file__).parent / "fixtures" / "test_robot.urdf"
