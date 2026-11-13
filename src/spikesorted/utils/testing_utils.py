"""Helpers for loading the repository's example recording."""

from pathlib import Path

import spikeinterface as si


def get_test_data(repo_path: str | Path):
    """Load the example recording, or explain how to download it."""
    repo_path = Path(repo_path)
    recording_path = repo_path / "tests/data/neuropixels-2010-spikeglx/si_recording"
    if not recording_path.is_dir():
        raise FileNotFoundError(
            f"Test recording not found: {recording_path}\n"
            "Run the following from the repository root in your Python environment:\n"
            "python tests/data/fetch_test_data.py"
        )

    return si.load(recording_path)
