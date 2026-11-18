"""Plots of recording data at each preprocessing stage."""

import matplotlib.pyplot as plt
import spikeinterface.widgets as sw


def plot_preprocessing_stages(recording, stages, user_operations, plots_path):
    """Plot one-second start, middle and end windows at every configured stage."""
    plots_path.mkdir()
    start = recording.get_start_time()
    duration = recording.get_duration()
    window = min(1.0, duration)
    middle_start = start + (duration - window) / 2
    time_ranges = {
        "start": (start, start + window),
        "middle": (middle_start, middle_start + window),
        "end": (start + duration - window, start + duration),
    }
    for name, time_range in time_ranges.items():
        window_path = plots_path / name
        window_path.mkdir()
        current = recording
        for index, operation in enumerate(["raw", *user_operations]):
            # Empty bad-channel operations are no-ops but still have a stage plot.
            current = stages.get(operation, current)
            widget = sw.plot_traces(
                current,
                time_range=time_range,
                mode="map",
                backend="matplotlib",
                return_in_uV=recording.has_scaleable_traces(),
            )
            try:
                widget.figure.suptitle(operation)
                widget.figure.savefig(window_path / f"{index:03d}_{operation}.png")
            finally:
                plt.close(widget.figure)
