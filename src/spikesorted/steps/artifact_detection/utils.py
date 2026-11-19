"""File loading and path helpers for artifact detection."""

from pathlib import Path

import numpy as np
import pandas as pd
from spikeinterface.core.base import base_period_dtype

from spikesorted.utils.output_paths import get_step_output_path
from spikesorted.utils.utils import message_user


def load_and_check_artefact_periods(
    output_path, config, session_name, shank_id, recording, verbose=False
) -> np.ndarray:
    """Validate saved artefact times and return SpikeInterface sample periods."""
    periods_path = get_artifact_periods_filepath(
        get_step_output_path(
            output_path,
            config,
            "artifact_detection",
            session_name,
            shank_id,
        )
    )
    if not periods_path.is_file():
        raise FileNotFoundError(f"Artefact CSV not found: {periods_path}")

    message_user(
        f"Loading artefact periods from: {periods_path}",
        verbose,
    )

    # check_artifact_period_times
    periods = pd.read_csv(periods_path)
    if not periods.empty:
        for sample_column, time_column in (
            ("start_sample_index", "start_time"),
            ("end_sample_index", "stop_time"),
        ):
            times = recording.sample_index_to_time(periods[sample_column].to_numpy())
            # Check within arbitrary, small tolerance
            if not np.allclose(times, periods[time_column], rtol=0, atol=1e-8):
                raise ValueError(
                    f"Artefact {sample_column} does not match "
                    f"{time_column}: {periods_path}"
                )

    si_periods = np.zeros(len(periods), dtype=base_period_dtype)
    for column in ("start_sample_index", "end_sample_index"):
        si_periods[column] = periods[column].to_numpy()
    return si_periods


def get_artifact_periods_filepath(shank_path: Path) -> Path:
    """Return the event-periods CSV path for a shank output directory."""
    return shank_path / "event_periods.csv"


def save_artefact_periods(shank_path, periods, recording, label):
    """Save sample periods with corresponding recording times and labels."""
    periods_df = pd.DataFrame(
        {
            "start_sample_index": periods["start_sample_index"],
            "end_sample_index": periods["end_sample_index"],
            "start_time": recording.sample_index_to_time(periods["start_sample_index"]),
            "stop_time": recording.sample_index_to_time(periods["end_sample_index"]),
            "label": label,
        }
    )
    periods_df.to_csv(get_artifact_periods_filepath(shank_path), index=False)
