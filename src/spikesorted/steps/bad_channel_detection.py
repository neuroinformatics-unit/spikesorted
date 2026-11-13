"""Bad-channel detection step (not implemented yet)."""

import sys
import warnings
from contextlib import redirect_stdout
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import ClassVar

import pandas as pd

# Preload SciPy signal so its one-time import allocations are process baseline,
# rather than part of the first bad-channel detection chunk.
import scipy.signal  # noqa: F401
import spikeinterface.preprocessing as spre
import yaml

from spikesorted.steps.base import BasePipelineStep
from spikesorted.utils.recordings_structure import get_num_sessions


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

    See Also
    --------
    BasePipelineStep
    spikeinterface.preprocessing.detect_bad_channels

    Notes
    -----
    The following CSV files are saved for each session and shank:

    ``bad_channel_ids.csv``
        One row per detected bad channel, with ``channel_id``
        and ``channel_id_dtype`` columns storing the identifier and NumPy dtype.

    ``bad_channel_labels.csv``
        One row per recording channel, including good channels, with
        columns ``channel_id``, ``label`` and ``channel_id_dtype``.
        Labels are supplied by SpikeInterface's ``detect_bad_channels()``.

    Both files include column headers and omit the DataFrame index.

    """

    _step_name: ClassVar[str] = "bad_channel_detection"

    def run(self, verbose: bool = True) -> None:
        """Check inputs, high-pass at 300 Hz, and run IBL bad-channel detection.

        Save channel IDs, labels, detection metrics, and associated plots.
        """
        self.perform_checks()

        kwargs = self.config["bad_channel_detection"]

        for (
            session_name,
            shank_id,
            shank_recording,
            shank_path,
        ) in self._get_recordings_and_paths():
            if verbose:
                shank_id_message = f", shank {shank_id}" if shank_id else ""
                print(
                    f"Running bad channel detection for session {session_name}"
                    + shank_id_message,
                    file=sys.stderr,
                    flush=True,
                )

            bad_ids_path = self.get_bad_channel_ids_filepath(shank_path)
            labels_path = self.get_bad_channel_labels_filepath(shank_path)

            shank_path.mkdir(parents=True, exist_ok=True)

            with redirect_stdout(sys.stderr):
                filtered_recording = spre.highpass_filter(
                    shank_recording, freq_min=self._highpass_freq_min
                )

                bad_channel_ids, channel_labels = spre.detect_bad_channels(
                    filtered_recording, **kwargs
                )

            channel_id_dtype = shank_recording.get_channel_ids().dtype.str
            bad_ids_df = pd.DataFrame(
                {
                    "channel_id": bad_channel_ids,
                    "channel_id_dtype": channel_id_dtype,
                }
            )
            labels_df = pd.DataFrame(
                {
                    "channel_id": shank_recording.get_channel_ids(),
                    "label": channel_labels,
                    "channel_id_dtype": channel_id_dtype,
                }
            )
            bad_ids_df.to_csv(bad_ids_path, index=False)
            labels_df.to_csv(labels_path, index=False)

            if verbose:
                print(
                    f"Bad channel IDS and labels saved to: {bad_ids_path.parent}",
                    file=sys.stderr,
                    flush=True,
                )

        if "combine_sessions" in self.config and get_num_sessions(self.recordings) > 1:
            self.create_bad_channel_labels_union()

    def perform_checks(self) -> None:
        """Check the bad-channel detection input:

        - checks required bad channel detection method is passed
        - throw a warning for low-coutn channels
        - raise if `overwrite=False` and output already exists.
        """
        super().perform_checks()

        method = self.config["bad_channel_detection"].get("method")
        if method is None:
            raise ValueError("bad_channel_detection.method must be explicitly provided")

        for _, _, recording, shank_path in self._get_recordings_and_paths():
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

            if not self.overwrite:
                if shank_path.exists():
                    raise FileExistsError(
                        "Bad-channel detection output folder already exists: "
                        f"{shank_path}. "
                        "Set overwrite=True to replace existing outputs, "
                        "or choose a different output_path."
                    )

    def load_bad_channels(self, session_name, shank_id=None):
        """Load bad-channel IDs for a session and shank in their original dtype."""
        channel_ids_path = (
            self._get_output_path(session_name, shank_id) / "bad_channel_ids.csv"
        )

        if not channel_ids_path.exists():
            return None

        bad_channels = pd.read_csv(channel_ids_path, dtype={"channel_id": str})

        bad_channel_ids = bad_channels["channel_id"].to_numpy()

        if not bad_channels.empty:
            # Bad channels can be str or int dtype
            bad_channels_type = bad_channels["channel_id_dtype"].iloc[0]
            bad_channel_ids = bad_channel_ids.astype(bad_channels_type)

        return bad_channel_ids

    def get_bad_channel_ids_filepath(self, shank_path: Path) -> Path:
        """Return the bad-channel IDs CSV path for a shank output directory."""
        return shank_path / "bad_channel_ids.csv"

    def get_bad_channel_labels_filepath(self, shank_path: Path) -> Path:
        """Return the all-channel labels CSV path for a shank output directory."""
        return shank_path / "bad_channel_labels.csv"

    def needs_gpu(self) -> bool:
        """Report whether the configured detection method requires a GPU."""
        return False

    def create_bad_channel_labels_union(self):
        """Create a CSV which contains the union of all bad channel IDs across sessions.

        When working with multiple sessions, and concatenating or unit-matching, the
        same set of channels must be included on all used recordings. This function
        uses the individual sessions bad channel detection outputs on disk to create
        a union of all bad channel labels.

        Outputs use "session_unions" as the session name in the configured layout.
        A sessions.yaml beside each CSV records the contributing session names and date.

        This step will throw an error if the set of sessions / shanks on disk
        does not exactly match those in `recordings`, as this may indicate the
        project has gotten out of sync.
        """
        recordings_by_shank = {}
        for session_name, shank_id, recording, path in self._get_recordings_and_paths():
            recordings_by_shank.setdefault(shank_id, []).append(
                (session_name, recording, path)
            )

        self._confirm_all_and_only_specified_bad_channel_files_exist(
            recordings_by_shank
        )

        # For each session / shank, load the bad channel ids and save their
        # union in the shared output folder
        generation_date = date.today().isoformat()

        for shank_id, recordings_and_paths in recordings_by_shank.items():
            bad_channel_ids = {}
            session_names = []

            for session_name, _, path in recordings_and_paths:
                session_names.append(session_name)
                labels = pd.read_csv(
                    path / "bad_channel_ids.csv",
                    dtype={"channel_id": str},
                    keep_default_na=False,
                )
                bad_channel_ids.update(
                    zip(labels["channel_id"], labels["channel_id_dtype"], strict=False)
                )

            output_path = self._get_output_path("session_unions", shank_id)

            output_path.mkdir(parents=True, exist_ok=True)

            pd.DataFrame(
                sorted(bad_channel_ids.items()),
                columns=["channel_id", "channel_id_dtype"],
            ).to_csv(output_path / "bad_channel_ids.csv", index=False)
            with (output_path / "sessions.yaml").open("w", encoding="utf-8") as file:
                yaml.safe_dump(
                    {"sessions": session_names, "date": generation_date},
                    file,
                    sort_keys=False,
                )

    def _confirm_all_and_only_specified_bad_channel_files_exist(
        self, recordings_by_shank
    ):
        """Require the discovered CSVs to match the supplied sessions/shanks exactly."""
        expected_files = sorted(
            path / "bad_channel_ids.csv"
            for recordings_and_paths in recordings_by_shank.values()
            for _, _, path in recordings_and_paths
        )

        root = Path(self.output_path)
        existing_files = set()
        union_files = set()
        for shank_id in (None, "*"):
            pattern = self._get_output_path("*", shank_id).relative_to(root)
            existing_files.update(root.glob(str(pattern / "bad_channel_ids.csv")))
            union_pattern = self._get_output_path(
                "session_unions", shank_id
            ).relative_to(root)
            union_files.update(root.glob(str(union_pattern / "bad_channel_ids.csv")))
        existing_files = sorted(existing_files - union_files)

        if expected_files != existing_files:
            missing = sorted(set(expected_files) - set(existing_files))
            unexpected = sorted(set(existing_files) - set(expected_files))
            raise ValueError(
                "Cannot create the bad-channel union: files in the project path "
                "do not match the supplied recordings.\n"
                f"Missing files: {missing}\n"
                f"Unexpected files: {unexpected}\n"
                "Remove folders for sessions or shanks that are not part of this run, "
                "and generate any missing bad-channel files before trying again."
            )
