"""
Basic functionality tests that don't require heavy dependencies.
These tests focus on core functionality for the Metro Power dashboard project.
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def test_python_version():
    """Test that we're running a supported Python version."""
    assert sys.version_info >= (3, 8), "Python 3.8+ is required"


def test_project_structure():
    """Test that essential project directories exist."""
    project_root = Path(__file__).parent.parent

    # Check for essential directories
    assert (project_root / "agents").exists(), "agents directory should exist"
    assert (project_root / "api").exists(), "api directory should exist"
    assert (project_root / "config").exists(), "config directory should exist"
    assert (project_root / "models").exists(), "models directory should exist"
    assert (project_root / "services").exists(), "services directory should exist"
    assert (project_root / "tests").exists(), "tests directory should exist"


def test_main_file_exists():
    """Test that main.py exists and is readable."""
    project_root = Path(__file__).parent.parent
    main_file = project_root / "main.py"

    assert main_file.exists(), "main.py should exist"
    assert main_file.is_file(), "main.py should be a file"

    # Test that it's readable
    content = main_file.read_text()
    assert len(content) > 0, "main.py should not be empty"


def test_config_files_exist():
    """Test that configuration files exist."""
    project_root = Path(__file__).parent.parent

    assert (project_root / "pyproject.toml").exists(), "pyproject.toml should exist"
    assert (project_root / ".flake8").exists(), ".flake8 should exist"
    assert (
        project_root / ".pre-commit-config.yaml"
    ).exists(), ".pre-commit-config.yaml should exist"


def test_requirements_file_exists():
    """Test that requirements.txt exists."""
    project_root = Path(__file__).parent.parent
    requirements_file = project_root / "requirements.txt"

    assert requirements_file.exists(), "requirements.txt should exist"

    # Test that it contains some dependencies
    content = requirements_file.read_text()
    assert "pydantic" in content.lower(), "requirements.txt should contain pydantic"


def test_basic_imports():
    """Test basic imports that should work without external dependencies."""
    try:
        import json
        import os
        import sys
        from datetime import datetime
        from pathlib import Path

        assert True, "Basic imports work"
    except ImportError as e:
        pytest.fail(f"Basic imports failed: {e}")


def test_models_directory_structure():
    """Test that models directory has expected files."""
    project_root = Path(__file__).parent.parent
    models_dir = project_root / "models"

    # Check for some key model files
    expected_files = [
        "base.py",
        "content_models.py",
        "task_models.py",
        "video_models.py",
    ]

    for file_name in expected_files:
        file_path = models_dir / file_name
        assert file_path.exists(), f"{file_name} should exist in models directory"


def test_metro_power_dashboard_readiness():
    """Test that the project is ready for Metro Power dashboard development."""
    project_root = Path(__file__).parent.parent

    # Check for essential components for dashboard development
    assert (project_root / "api").exists(), "API directory needed for dashboard backend"
    assert (
        project_root / "models"
    ).exists(), "Models directory needed for data structures"
    assert (
        project_root / "services"
    ).exists(), "Services directory needed for business logic"

    # Check that we have configuration management
    assert (project_root / "config").exists(), "Config directory needed for settings"

    # Check for frontend directory (for dashboard UI)
    assert (
        project_root / "frontend"
    ).exists(), "Frontend directory needed for dashboard UI"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
