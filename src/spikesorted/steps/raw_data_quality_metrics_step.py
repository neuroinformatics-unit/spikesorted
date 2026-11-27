"""Raw-data quality metrics step for one session shank."""

from __future__ import annotations

import sys
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from spikeinterface import load
from spikeinterface.qualitycontrol import raw_data_quality_metrics

from spikesorted.steps.bad_channel_detection import (
    BadChannelDetectionStep,
    BadChannelUnionStep,
)
from spikesorted.steps.bad_channel_detection.utils import (
    get_bad_channel_ids_filepath,
    load_and_check_bad_channel_ids,
)
from spikesorted.steps.input_data_step import InputDataStep
from spikesorted.utils.output_paths import get_step_output_path
from spikesorted.utils.utils import load_pipeline_config, message_user

if TYPE_CHECKING:
    from spikesorted.validation.config_validation import PipelineConfig


@dataclass(frozen=True)
class RawDataQualityMetricsStep:
    """Compute and save raw-data quality metrics for one session and shank.

    The ``run()`` method wraps SpikeInterface's ``raw_data_quality_metrics()``,
    which saves RMS summaries as CSVs and a quality plot. When the config
    includes ``bad_channel_detection``, the detected bad channels are removed
    from the recording first.

    Parameters
    ----------
    session_name
        Name of the session to process.

    shank_id
        ID of the shank to process.

    config_path
        Path to the YAML pipeline configuration file containing the
        ``raw_data_quality_metrics`` settings.

    output_path
        The subject folder. The input recording is read from the session
        shank's ``input_data`` folder, and outputs are written beside it.

    See Also
    --------
    spikeinterface.qualitycontrol.raw_data_quality_metrics

    Examples
    --------
    >>> RawDataQualityMetricsStep(
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

    _step_name: ClassVar[str] = "raw_data_quality_metrics"

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
        cls,
        output_path: str | Path,
        config: PipelineConfig,
        session_name: str,
        shank_id: str,
    ) -> list[Path]:
        """Return the paths this step waits for, for a session shank.

        Parameters
        ----------
        output_path
            The subject folder.
        config
            The loaded pipeline config.
        session_name
            Name of the session.
        shank_id
            Shank ID.

        Returns
        -------
        input_paths
            The CSV holding the bad channels to remove when the config
            includes ``bad_channel_detection``: the shank's union CSV and session
            metadata with ``combine_sessions``, otherwise the session shank's
            bad-channel detection CSV. Without ``bad_channel_detection``, the session
            shank's ``recording.json`` and ``recording_info.yaml``.
        """
        if "bad_channel_detection" in config:
            if "combine_sessions" in config:
                union_path = BadChannelUnionStep.get_output_path(output_path, shank_id)
                return [
                    get_bad_channel_ids_filepath(union_path),
                    union_path / "sessions.yaml",
                ]
            else:
                return [
                    get_bad_channel_ids_filepath(
                        BadChannelDetectionStep.get_output_path(
                            output_path, session_name, shank_id
                        )
                    )
                ]
        else:
            return [
                InputDataStep.get_recording_json_path(
                    output_path, session_name, shank_id
                ),
                InputDataStep.get_recording_info_path(
                    output_path, session_name, shank_id
                ),
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
            The session shank's raw-data quality metrics folder.
        """
        return get_step_output_path(output_path, cls._step_name, session_name, shank_id)

    def run(self, verbose: bool = True) -> None:
        """Remove bad channels and save SI's metric summaries and plots.

        Parameters
        ----------
        verbose
            Whether to print progress messages.
        """
        metrics_kwargs = self.config["raw_data_quality_metrics"]

        shank_path = self.get_output_path(
            self.output_path, self.session_name, self.shank_id
        )
        shank_id_message = f", shank {self.shank_id}" if self.shank_id else ""
        message_user(
            f"Running raw-data quality metrics for session {self.session_name}"
            + shank_id_message,
            verbose,
        )

        with redirect_stdout(sys.stderr):
            shank_recording = load(
                InputDataStep.get_recording_json_path(
                    self.output_path, self.session_name, self.shank_id
                )
            )

        if "bad_channel_detection" in self.config:
            bad_channel_ids = load_and_check_bad_channel_ids(
                self.output_path,
                self.config,
                self.session_name,
                self.shank_id,
                required=True,
            )
            if len(bad_channel_ids) != 0:
                shank_recording = shank_recording.remove_channels(bad_channel_ids)

        with redirect_stdout(sys.stderr):
            raw_data_quality_metrics(
                shank_recording, folder=shank_path, verbose=verbose, **metrics_kwargs
            )

        message_user(
            f"Raw-data quality metrics saved to: {shank_path}",
            verbose,
        )

    def needs_gpu(self) -> bool:
        """Report whether raw-data quality metrics require a GPU."""
        return False
