"""Bad-channel detection step for one session shank."""

from __future__ import annotations

import sys
import warnings
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

# Preload SciPy signal so its one-time import allocations are process baseline,
# rather than part of the first bad-channel detection chunk.
import scipy.signal  # noqa: F401
import spikeinterface.preprocessing as spre
from spikeinterface import load

from spikesorted.steps.input_data_step import InputDataStep
from spikesorted.utils.output_paths import get_step_output_path
from spikesorted.utils.utils import load_pipeline_config, message_user

from .utils import (
    get_bad_channel_ids_filepath,
    save_bad_channel_ids,
    save_bad_channel_labels,
)

if TYPE_CHECKING:
    from spikesorted.validation.config_validation import PipelineConfig


@dataclass(frozen=True)
class BadChannelDetectionStep:
    """Detect bad channels for one session and shank.

    The ``run()`` method wraps SpikeInterface's ``detect_bad_channels()``.

    Parameters
    ----------
    session_name
        Name of the session to process.

    shank_id
        ID of the shank to process.

    config_path
        Path to the YAML pipeline configuration file containing the
        ``bad_channel_detection`` settings.

    output_path
        The subject folder. The input recording is read from the session
        shank's ``input_data`` folder, and outputs are written beside it.

    See Also
    --------
    spikeinterface.preprocessing.detect_bad_channels

    Notes
    -----
    The following CSV files are saved for the session shank:

    ``bad_channel_ids.csv``
        One row per detected bad channel, with ``channel_id``
        and ``channel_id_dtype`` columns storing the identifier and NumPy dtype.

    ``bad_channel_labels.csv``
        One row per recording channel, including good channels, with
        columns ``channel_id``, ``label`` and ``channel_id_dtype``.
        Labels are supplied by SpikeInterface's ``detect_bad_channels()``.

    Both files include column headers and omit the DataFrame index.

    Examples
    --------
    >>> BadChannelDetectionStep(
    ...     session_name="ses-001",
    ...     shank_id="0",
    ...     config_path="config.yaml",
    ...     output_path="/derivatives/sub-001",
    ... ).run()
    """

    session_name: str
    shank_id: str
    config_path: str | Path
    output_path: str | Path

    _step_name: ClassVar[str] = "bad_channel_detection"

    _highpass_freq_min: ClassVar[float] = 300

    _config: PipelineConfig = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Load and validate the pipeline config once."""
        object.__setattr__(self, "_config", load_pipeline_config(self.config_path))

    @property
    def config(self) -> PipelineConfig:
        """Return the dictionary loaded at construction, without rereading disk."""
        return self._config

    @classmethod
    def get_input_paths(
        cls, output_path: str | Path, session_name: str, shank_id: str
    ) -> list[Path]:
        """Return the input data files this step reads for a session shank.

        Parameters
        ----------
        output_path
            The subject folder.
        session_name
            Name of the session.
        shank_id
            Shank ID.

        Returns
        -------
        input_paths
            The session shank's ``recording.json`` and ``recording_info.yaml``.
        """
        return [
            InputDataStep.get_recording_json_path(output_path, session_name, shank_id),
            InputDataStep.get_recording_info_path(output_path, session_name, shank_id),
        ]

    @classmethod
    def get_output_path(
        cls, output_path: str | Path, session_name: str, shank_id: str
    ) -> Path:
        """Return the folder this step writes for a session shank.

        Parameters
        ----------
        output_path
            The subject folder.
        session_name
            Name of the session.
        shank_id
            Shank ID.

        Returns
        -------
        step_path
            The session shank's bad-channel detection folder.
        """
        return get_step_output_path(output_path, cls._step_name, session_name, shank_id)

    def run(self, verbose: bool = True) -> None:
        """Check inputs, high-pass at 300 Hz, and run IBL bad-channel detection.

        Save channel IDs and labels.

        Parameters
        ----------
        verbose
            Whether to print progress messages.
        """
        self.perform_checks()

        detection_kwargs = self.config["bad_channel_detection"]

        shank_path = self.get_output_path(
            self.output_path, self.session_name, self.shank_id
        )
        shank_id_message = f", shank {self.shank_id}" if self.shank_id else ""
        message_user(
            f"Running bad channel detection for session {self.session_name}"
            + shank_id_message,
            verbose,
        )

        bad_channel_ids_path = get_bad_channel_ids_filepath(shank_path)

        shank_path.mkdir(parents=True, exist_ok=True)

        with redirect_stdout(sys.stderr):
            shank_recording = load(self._get_recording_json_path())

            filtered_recording = spre.highpass_filter(
                shank_recording, freq_min=self._highpass_freq_min
            )

            bad_channel_ids, channel_labels = spre.detect_bad_channels(
                filtered_recording, **detection_kwargs
            )

        channel_id_dtype = shank_recording.get_channel_ids().dtype.str
        save_bad_channel_ids(shank_path, bad_channel_ids, channel_id_dtype)
        save_bad_channel_labels(
            shank_path,
            shank_recording.get_channel_ids(),
            channel_labels,
            channel_id_dtype,
        )

        message_user(
            f"Bad channel IDS and labels saved to: {bad_channel_ids_path.parent}",
            verbose,
        )

    def perform_checks(self) -> None:
        """Check the bad-channel detection input:

        - checks the input data files exist
        - checks required bad channel detection method is passed
        - throw a warning for low-count channels
        """
        for input_path in self.get_input_paths(
            self.output_path, self.session_name, self.shank_id
        ):
            if not input_path.is_file():
                raise FileNotFoundError(
                    f"Input data file not found: {input_path}. "
                    "Run the input data step for this session first."
                )

        detection_method = self.config["bad_channel_detection"].get("method")
        if detection_method is None:
            raise ValueError("bad_channel_detection.method must be explicitly provided")

        with redirect_stdout(sys.stderr):
            recording = load(self._get_recording_json_path())

        num_channels = recording.get_num_channels()
        if detection_method == "coherence+psd" and num_channels <= 64:
            warnings.warn(
                f"Recording for session {self.session_name}, shank "
                f"{self.shank_id} has {num_channels} channels "
                "(64 or fewer). IBL bad-channel detection was developed for "
                "Neuropixels probes; review its suitability and thresholds "
                "for low-channel-count recordings.",
                UserWarning,
                stacklevel=2,
            )

    def needs_gpu(self) -> bool:
        """Report whether the configured detection method requires a GPU."""
        return False

    def _get_recording_json_path(self) -> Path:
        """Return the input recording for this session shank.

        Returns
        -------
        recording_json_path
            Path of the session shank's ``recording.json``.
        """
        return InputDataStep.get_recording_json_path(
            self.output_path, self.session_name, self.shank_id
        )
