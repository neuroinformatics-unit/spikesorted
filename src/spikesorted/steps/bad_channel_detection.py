"""Bad-channel detection step (not implemented yet)."""

import warnings
from dataclasses import dataclass
from math import ceil
from pathlib import Path

import pandas as pd

# Preload SciPy signal so its one-time import allocations are process baseline,
# rather than part of the first bad-channel detection chunk.
import scipy.signal  # noqa: F401
import spikeinterface.preprocessing as spre

from ...utils.recordings_structure import get_num_sessions
from ..base import BasePipelineStep
from .bad_channel_union import create_bad_channel_labels_union
from .estimate_bad_channel_detection_memory_usage import (
    estimate_bad_channel_detection_memory_usage,
    estimate_filter_memory_usage,
    _parameter,
)


@dataclass(frozen=True)
class BadChannelDetectionStep(BasePipelineStep):
    """Detect bad channels for each recording session and shank.

    The ``run()`` method wraps SpikeInterface's ``detect_bad_channels()``.

    Parameters
    ----------
    recordings : RecordingInput or list of RecordingInput
        A recording, a dictionary mapping shank IDs to recordings, or a
        tuple of (recording or shank dictionary, session name). Supply a
        list of these objects to process multiple sessions.

    config_path : str or pathlib.Path
        Path to the YAML pipeline configuration file containing the
        ``bad_channel_detection`` settings.

    output_path : str or pathlib.Path
        Root output directory under which the step saves outputs for
        each session and shank.

    overwrite : bool, optional
        Whether to overwrite existing output CSV files. Default is False.

    num_cores : int, optional
        Number of CPU cores allocated to the step. Default is 1.

    See Also
    --------
    BasePipelineStep
    spikeinterface.preprocessing.detect_bad_channels

    Notes
    -----
    The following CSV files are saved for each session and shank:

    ``bad_channel_ids.csv``
        One row per detected bad channel, with a single ``channel_id``
        column containing its SpikeInterface channel identifier.

    ``bad_channel_labels.csv``
        One row per recording channel, including good channels, with
        columns ``channel_id`` and ``label``. Labels are supplied by
        SpikeInterface's ``detect_bad_channels()``.

    Both files include column headers and omit the DataFrame index.
    """
    def run(self, verbose: bool = True) -> None:
        """Check inputs, high-pass at 300 Hz, and run IBL bad-channel detection.

        Save channel IDs, labels, detection metrics, and associated plots.
        """
        self.perform_checks()

        kwargs = self.config["bad_channel_detection"]

        for session_name, shank_id, shank_recording, shank_path in self._get_recordings_and_paths(
            "bad_channel_detection"
        ):
            if verbose:
                shank_id_message = f", shank {shank_id}" if shank_id else ""
                print(f"Running bad channel detection for session {session_name}" + shank_id_message)

            bad_ids_path = self.get_bad_channel_ids_filepath(shank_path)
            labels_path = self.get_bad_channel_labels_filepath(shank_path)

            shank_path.mkdir(parents=True, exist_ok=True)

            filtered_recording = spre.highpass_filter(shank_recording, freq_min=self._highpass_freq_min)

            bad_channel_ids, channel_labels = spre.detect_bad_channels(
                filtered_recording, **kwargs
            )

            bad_ids_df = pd.DataFrame({"channel_id": bad_channel_ids})
            labels_df = pd.DataFrame(
                {
                    "channel_id": shank_recording.get_channel_ids(),
                    "label": channel_labels,
                }
            )
            bad_ids_df.to_csv(bad_ids_path, index=False)
            labels_df.to_csv(labels_path, index=False)

            if verbose:
                print(f"Bad channel IDS and labels saved to: {bad_ids_path.parent}")

        if "combine_sessions" in self.config and get_num_sessions(self.recordings) > 1:
            create_bad_channel_labels_union(self.recordings, self.output_path)

    def perform_checks(self) -> None:
        """This function performs the following checks on the bad channel detction intput:

        - checks required bad channel detection method is passed
        - throw a warning for low-coutn channels
        - raise if `overwrite=False` and output already exists.
        """
        method = self.config["bad_channel_detection"].get("method")
        if method is None:
            raise ValueError("bad_channel_detection.method must be explicitly provided")

        for recording, shank_path in self._get_recordings_and_paths(
            "bad_channel_detection"
        ):

            num_channels = recording.get_num_channels()
            if method == "coherence+psd" and num_channels <= 64:
                warnings.warn(
                    f"Recording for {shank_path} has {num_channels} channels "
                    "(64 or fewer). IBL bad-channel detection was developed for "
                    "Neuropixels probes; review its suitability and thresholds "
                    "for low-channel-count recordings.",
                    UserWarning,
                    stacklevel=2,
                )

            bad_ids_path = self.get_bad_channel_ids_filepath(shank_path)
            labels_path = self.get_bad_channel_labels_filepath(shank_path)

            if not self.overwrite:
                for output_path in (bad_ids_path, labels_path):
                    if output_path.exists():
                        raise FileExistsError(
                            "Bad-channel detection output already exists: "
                            f"{output_path}. "
                            "Set overwrite=True to replace existing outputs, "
                            "or choose a different output_path."
                        )

    def get_bad_channel_ids_filepath(self, shank_path: Path) -> Path:
        """Return the bad-channel IDs CSV path for a shank output directory."""
        return shank_path / "bad_channel_ids.csv"

    def get_bad_channel_labels_filepath(self, shank_path: Path) -> Path:
        """Return the all-channel labels CSV path for a shank output directory."""
        return shank_path / "bad_channel_labels.csv"

    def needs_gpu(self) -> bool:
        """Report whether the configured detection method requires a GPU."""
        return False

