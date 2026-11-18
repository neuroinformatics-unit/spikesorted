"""Artifact detection step."""

import sys
import warnings
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import numpy as np
import pandas as pd
import spikeinterface.preprocessing as spre

from spikesorted.plotting.artifact_detection import save_artifact_plots

from .bad_channel_detection import BadChannelDetectionStep
from .base import BasePipelineStep


@dataclass(frozen=True)
class ArtifactDetectionStep(BasePipelineStep):
    """ """

    _step_name: ClassVar[str] = "artifact_detection"

    def run(self, verbose: bool = True) -> None:
        """Detect saturation periods and save sample indices and times in seconds."""
        self.perform_checks()

        bad_channel_detection = BadChannelDetectionStep(
            recordings=self.recordings,
            config_path=self.config_path,
            output_path=self.output_path,
        )

        saturation_kwargs = self.config["artifact_detection"].get("saturation")

        for (
            session_name,
            shank_id,
            shank_recording,
            shank_path,
        ) in self._get_recordings_and_paths():
            if verbose:
                shank_id_message = f", shank {shank_id}" if shank_id else ""
                print(
                    f"Running artifact detection for session {session_name}"
                    + shank_id_message,
                    file=sys.stderr,
                    flush=True,
                )

            periods_path = self.get_artifact_periods_filepath(shank_path)
            shank_path.mkdir(parents=True, exist_ok=True)

            # Remove bad channels if they exist
            bad_channel_ids = bad_channel_detection.load_bad_channels(
                session_name, shank_id
            )
            if bad_channel_ids is None:
                warnings.warn(
                    f"No bad channel ids found for session {session_name}, "
                    f"shank {shank_id}. "
                    "Bad channels not removed before artifact detection.",
                    stacklevel=2,
                )
            elif len(bad_channel_ids) != 0:
                shank_recording = shank_recording.remove_channels(bad_channel_ids)

            # Perform artefact detection and save the results to CSV
            with redirect_stdout(sys.stderr):
                periods = spre.detect_artifact_periods(
                    shank_recording,
                    method="saturation",
                    method_kwargs=saturation_kwargs,
                )

            periods_df = pd.DataFrame(
                {
                    "start_sample_index": periods["start_sample_index"],
                    "end_sample_index": periods["end_sample_index"],
                    "start_time": shank_recording.sample_index_to_time(
                        periods["start_sample_index"]
                    ),
                    "stop_time": shank_recording.sample_index_to_time(
                        periods["end_sample_index"]
                    ),
                    "label": "SATURATION",
                }
            )
            periods_df.to_csv(periods_path, index=False)

            # Create a plot of a few artefacts and save this to disk.
            save_artifact_plots(shank_recording, periods, shank_path)

            if verbose:
                print(
                    f"Artifact periods saved to: {periods_path}",
                    file=sys.stderr,
                    flush=True,
                )

    def perform_checks(self) -> None:
        """ """
        super().perform_checks()

        all_kwargs = self.config["artifact_detection"]
        saturation_kwargs = all_kwargs.get("saturation")
        if saturation_kwargs is None:
            raise ValueError("Must pass `saturation` option for artifact detection.")

        envelope_kwargs = all_kwargs.get("envelope")
        if envelope_kwargs:
            raise NotImplementedError(
                "`envelope` option for artifact detection is not currently supported."
            )

        if not self.overwrite:
            for _, _, _, shank_path in self._get_recordings_and_paths():
                if shank_path.exists():
                    raise FileExistsError(
                        "Artifact detection output folder already exists: "
                        f"{shank_path}. "
                        "Set overwrite=True to replace existing outputs, "
                        "or choose a different output_path."
                    )

    def load_artifacts_against_recording(
        self, session_name, shank_id, recording
    ) -> pd.DataFrame:
        """Load saved artefact periods and check their times against a recording."""
        periods_path = self.get_artifact_periods_filepath(
            self._get_output_path(session_name, shank_id)
        )
        if not periods_path.is_file():
            raise FileNotFoundError(f"Artefact CSV not found: {periods_path}")

        # check_artifact_period_times
        periods = pd.read_csv(periods_path)
        if not periods.empty:
            for sample_column, time_column in (
                ("start_sample_index", "start_time"),
                ("end_sample_index", "stop_time"),
            ):
                times = recording.sample_index_to_time(
                    periods[sample_column].to_numpy()
                )
                # Check with for now arbitrary, small tolerance
                if not np.allclose(times, periods[time_column], rtol=0, atol=1e-8):
                    raise ValueError(
                        f"Artefact {sample_column} does not match "
                        f"{time_column}: {periods_path}"
                    )

        return periods

    def get_artifact_periods_filepath(self, shank_path: Path) -> Path:
        """Return the event-periods CSV path for a shank output directory."""
        return shank_path / "event_periods.csv"

    def needs_gpu(self) -> bool:
        """Report whether the configured detection method requires a GPU."""
        return False
