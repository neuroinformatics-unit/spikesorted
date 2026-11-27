"""Plots of detected artefact periods."""

import sys
from contextlib import redirect_stdout

import matplotlib.pyplot as plt
import numpy as np
import spikeinterface.widgets as sw


def plot_artifact_periods(recording, periods):
    """Plot up to six evenly spaced events with a shared time-window width."""
    num_artifacts = len(periods)
    if num_artifacts == 0:
        return None

    # Display up to 6 plots
    n_plots = min(num_artifacts, 6)
    n_rows = 1 if n_plots <= 3 else 2
    n_cols = (n_plots + n_rows - 1) // n_rows

    figure, axes = plt.subplots(
        n_rows,
        n_cols,
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
        selected_artifacts["end_sample_index"]
        - selected_artifacts["start_sample_index"]
    )
    window_samples = 3 * int(artifact_durations.max())
    half_window_samples = window_samples // 2

    # For each artefact, add to the subplot the data, with artefact
    # centered, and two lines indicated the start/stop of the period.
    for axis, period in zip(axes, selected_artifacts, strict=False):
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
        with redirect_stdout(sys.stderr):
            sw.plot_traces(
                recording,
                time_range=time_range,
                backend="matplotlib",
                ax=axis,
            )
        # draw a band at the detection period
        artefact_times = recording.sample_index_to_time(
            np.array(
                [
                    artefact_start,
                    min(artefact_stop, recording.get_num_samples() - 1),
                ]
            )
        )
        axis.axvspan(
            artefact_times[0],
            artefact_times[1],
            color="tab:orange",
            alpha=0.2,
        )
        axis.set_title(f"Artifact at {artefact_times[0]:.3f} s")

    return figure


def save_artifact_plots(recording, periods, output_path):
    """Save the artefact figure when detected periods are present."""
    figure = plot_artifact_periods(recording, periods)

    if figure is not None:
        plots_path = output_path / "artifact_detection_plots"
        plots_path.mkdir(parents=True, exist_ok=True)

        figure.savefig(plots_path / "artifact_periods.png", dpi=150)
        plt.close(figure)
