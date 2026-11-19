"""Plots of raw and preprocessed recording data."""

import matplotlib.pyplot as plt
import spikeinterface.widgets as sw


def plot_preprocessing(recording, processed, plots_path):
    """Plot one-second start, middle and end windows before and after preprocessing."""
    assert not plots_path.exists()

    plots_path.mkdir(parents=False, exist_ok=True)

    start = recording.get_start_time()
    duration = recording.get_duration()


    all_windows = [
        min(1.0, duration),
        min(0.1, duration)
    ]

    for window in all_windows:

        middle_start = start + (duration - window) / 2

        time_ranges = {
            "start": (start, start + window),
            "middle": (middle_start, middle_start + window),
            "end": (start + duration - window, start + duration),
        }

        for name, time_range in time_ranges.items():
            for label, current in (("raw", recording), ("prepro", processed)):

                widget = sw.plot_traces(
                    current,
                    time_range=time_range,
                    mode="map",
                    backend="matplotlib",
                    return_in_uV=recording.has_scaleable_traces(),
                )
                try:
                    # seconds for > 1 and ms for < 1
                    time_label = f"{window:g}s" if window >= 1 else f"{window * 1000:g}ms"
                    widget.figure.suptitle(label)
                    widget.figure.savefig(plots_path / f"{name}_{time_label}_{label}.png")
                finally:
                    plt.close(widget.figure)
