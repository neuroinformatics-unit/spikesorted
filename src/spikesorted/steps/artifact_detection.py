"""Artifact detection step."""

import warnings

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import spikeinterface.preprocessing as spre
import spikeinterface.widgets as sw

from .base import BasePipelineStep
from .bad_channel_detection import BadChannelDetectionStep


@dataclass(frozen=True)
class ArtifactDetectionStep(BasePipelineStep):
    """
    """
    def run(self, verbose: bool = True) -> None:
        """Detect saturation periods and save sample indices and times in seconds."""
        self.perform_checks()

        saturation_kwargs = self.config["artifact_detection"].get("saturation")

        for session_name, shank_id, shank_recording, shank_path in self._get_recordings_and_paths(
            "artifact_detection"
        ):
            if verbose:
                shank_id_message = f", shank {shank_id}" if shank_id else ""
                print(f"Running artifact detection for session {session_name}" + shank_id_message)

            periods_path = self.get_artifact_periods_filepath(shank_path)
            shank_path.mkdir(parents=True, exist_ok=True)

            # Remove bad channels if they exist
            bad_channel_ids = BadChannelDetectionStep.load_bad_channels(
                self.output_path, session_name, shank_id
            )
            if bad_channel_ids is None:
                warnings.warn(
                    f"No bad channel ids found for session {session_name}, shank {shank_id}. "
                    "Bad channels not removed before artifact detection."
                )
            elif len(bad_channel_ids) != 0:
                shank_recording = shank_recording.remove_channels(bad_channel_ids)

            # Perform artefact detection and save the results to CSV
            periods = spre.detect_artifact_periods(
                shank_recording, method="saturation", method_kwargs=saturation_kwargs
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
            figure = self._get_artifact_plots(
                shank_recording, periods
            )
            if figure is not None:
                plots_path = shank_path / "artifact_detection_plots"
                plots_path.mkdir(parents=True, exist_ok=True)

                figure.savefig(plots_path / "artifact_periods.png", dpi=150)
                plt.close(figure)

            if verbose:
                print(f"Artifact periods saved to: {periods_path}")

    def perform_checks(self) -> None:
        """
        """
        super().perform_checks()

        all_kwargs = self.config["artifact_detection"]
        saturation_kwargs = all_kwargs.get("saturation")
        if saturation_kwargs is None:
            raise ValueError("Must pass `saturation` option for artifact detection.")

        envelope_kwargs = all_kwargs.get("envelope")
        if envelope_kwargs:
            raise NotImplementedError("`envelope` option for artifact detection is not currently supported.")

        if not self.overwrite:
            for _, _, _, shank_path in self._get_recordings_and_paths(
                "artifact_detection"
            ):
                if shank_path.exists():
                    raise FileExistsError(
                        "Artifact detection output folder already exists: "
                        f"{shank_path}. "
                        "Set overwrite=True to replace existing outputs, "
                        "or choose a different output_path."
                    )

    def get_artifact_periods_filepath(self, shank_path: Path) -> Path:
        """Return the event-periods CSV path for a shank output directory."""
        return shank_path / "event_periods.csv"

    def needs_gpu(self) -> bool:
        """Report whether the configured detection method requires a GPU."""
        return False

    def _get_artifact_plots(self, recording, periods):
        """Plot up to six evenly spaced events with a shared time-window width."""
        num_artifacts = len(periods)
        if num_artifacts == 0:
            return None

        # Display up to 6 plots
        n_plots = min(num_artifacts, 6)
        n_rows = 1 if n_plots <= 3 else 2
        n_cols = (n_plots + n_rows - 1) // n_rows

        figure, axes = plt.subplots(
            n_rows, n_cols,
            figsize=(4 * n_cols, 3 * n_rows),
            squeeze=False,
            layout="constrained",
        )
        axes = axes.ravel()

        # Subselect artifacts distributed across the recording
        ordered = periods[np.argsort(periods["start_sample_index"])]
        selected_indices = np.linspace(0, num_artifacts - 1, n_plots, dtype=int)
        selected_artifacts = ordered[selected_indices]

        # Centre each artifact in a window three times the longest artifact
        artifact_durations = (
            selected_artifacts["end_sample_index"] - selected_artifacts["start_sample_index"]
        )
        window_samples = 3 * int(artifact_durations.max())
        half_window_samples = window_samples // 2

        # For each artefact, add to the subplot the data, with artefact
        # centered, and two lines indicated the start/stop of the period.
        for axis, period in zip(axes, selected_artifacts):
            artefact_start = int(period["start_sample_index"])
            artefact_stop = int(period["end_sample_index"])
            centre_sample = (artefact_start + artefact_stop) // 2

            first_sample = max(0, centre_sample - half_window_samples)
            last_sample = min(
                recording.get_num_samples() - 1,
                centre_sample + half_window_samples,
            )

            time_range = recording.sample_index_to_time(
                np.array([first_sample, last_sample])
            )
            sw.plot_traces(
                recording,
                time_range=time_range,
                backend="matplotlib",
                ax=axis,
            )
            # draw a band at the detection period
            artefact_times = recording.sample_index_to_time(
                np.array([
                    artefact_start,
                    min(artefact_stop, recording.get_num_samples() - 1),
                ])
            )
            axis.axvspan(
                artefact_times[0], artefact_times[1],
                color="tab:orange", alpha=0.2,
            )
            axis.set_title(f"Artifact at {artefact_times[0]:.3f} s")

        return figure
