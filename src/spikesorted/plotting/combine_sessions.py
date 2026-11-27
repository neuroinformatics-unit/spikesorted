"""Plots across concatenated session boundaries."""

import matplotlib.pyplot as plt
import spikeinterface.widgets as sw


def plot_concatenation_points(recording, sessions, plots_path):
    """Save a one-second window centred on each session boundary."""
    plots_path.mkdir(parents=False, exist_ok=True)
    sampling_frequency = recording.get_sampling_frequency()
    boundary_frame = 0

    for index in range(len(sessions) - 1):
        session_name, session = sessions[index]
        next_session_name, next_session = sessions[index + 1]
        boundary_frame += session.get_num_samples()
        boundary = boundary_frame / sampling_frequency

        time_range = (
            boundary - min(0.5, session.get_duration()),
            min(
                boundary + min(0.5, next_session.get_duration()),
                recording.get_end_time(),
            ),
        )
        widget = sw.plot_traces(
            recording,
            time_range=time_range,
            mode="map",
            backend="matplotlib",
            return_in_uV=recording.has_scaleable_traces(),
        )
        try:
            widget.ax.axvline(boundary, color="red", linestyle="--")
            widget.figure.suptitle(f"{session_name} → {next_session_name}")
            widget.figure.savefig(plots_path / f"boundary_{index + 1:03d}_1s.png")
        finally:
            plt.close(widget.figure)
