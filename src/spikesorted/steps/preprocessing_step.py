"""Preprocess one session shank using SpikeInterface's ordered pipeline."""

from __future__ import annotations

import copy
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import spikeinterface.preprocessing as spre
from spikeinterface import load

from spikesorted.plotting.preprocessing import plot_preprocessing
from spikesorted.step_configs import (
    SPATIAL_OPERATIONS,
    TEMPORAL_FILTERS,
)
from spikesorted.steps.artifact_detection import ArtifactDetectionStep
from spikesorted.steps.artifact_detection.utils import load_and_check_artefact_periods
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
class PreprocessingStep:
    """Preprocess one session and shank using the configured step order.

    The ``run()`` method wraps SpikeInterface's
    ``apply_preprocessing_pipeline()``, applying the steps of the config's
    ``preprocessing`` section in the order they are written.

    Parameters
    ----------
    session_name
        Name of the session to process.

    shank_id
        ID of the shank to process.

    config_path
        Path to the YAML pipeline configuration file containing the
        ``preprocessing`` settings.

    output_path
        The subject folder. The input recording is read from the session
        shank's ``input_data`` folder, and outputs are written beside it.

    See Also
    --------
    spikeinterface.preprocessing.apply_preprocessing_pipeline

    Notes
    -----
    The following are saved for the session shank:

    ``preprocessing_plots/``
        Traces before and after preprocessing, at the start, middle and end
        of the recording.

    ``recording/``
        The preprocessed data, saved when ``save_preprocessed_copy`` in the
        config's ``preprocessing`` section is true.

    ``metadata.json``
        A SpikeInterface JSON dump that later steps load the preprocessed
        recording from. When ``recording/`` is saved it points at that.
        Otherwise it points at the raw data and the preprocessing is
        recomputed on loading, so the raw data must stay where it is.

    Examples
    --------
    >>> PreprocessingStep(
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

    _step_name: ClassVar[str] = "preprocessing"

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
            The CSV holding the bad channels when the ``preprocessing`` section
            includes ``remove_bad_channels`` or ``interpolate_bad_channels``:
            the shank's union CSV and session metadata with
            ``combine_sessions``, otherwise the session shank's bad-channel
            detection CSV. The session shank's artifact detection folder when
            it includes ``silence_periods``. With neither, the session shank's
            ``recording.json`` and ``recording_info.yaml``.
        """
        preprocessing_steps = config["preprocessing"]

        input_paths = []

        if (
            "remove_bad_channels" in preprocessing_steps
            or "interpolate_bad_channels" in preprocessing_steps
        ):
            if "combine_sessions" in config:
                union_path = BadChannelUnionStep.get_output_path(output_path, shank_id)
                input_paths.append(get_bad_channel_ids_filepath(union_path))
                input_paths.append(union_path / "sessions.yaml")
            else:
                input_paths.append(
                    get_bad_channel_ids_filepath(
                        BadChannelDetectionStep.get_output_path(
                            output_path, session_name, shank_id
                        )
                    )
                )

        if "silence_periods" in preprocessing_steps:
            input_paths.append(
                ArtifactDetectionStep.get_output_path(
                    output_path, session_name, shank_id
                )
            )

        if len(input_paths) == 0:
            input_paths.append(
                InputDataStep.get_recording_json_path(
                    output_path, session_name, shank_id
                )
            )
            input_paths.append(
                InputDataStep.get_recording_info_path(
                    output_path, session_name, shank_id
                )
            )

        return input_paths

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
            The session shank's preprocessing folder.
        """
        return get_step_output_path(output_path, cls._step_name, session_name, shank_id)

    def run(self, verbose: bool = True) -> None:
        """Preprocess the recording and save its plots, metadata and optional copy.

        Parameters
        ----------
        verbose
            Whether to print progress messages.
        """
        self.perform_checks()

        step_path = self.get_output_path(
            self.output_path, self.session_name, self.shank_id
        )
        shank_message = f", shank {self.shank_id}" if self.shank_id else ""
        message_user(
            f"Preprocessing session {self.session_name}{shank_message}",
            verbose,
        )

        step_path.mkdir(parents=True, exist_ok=True)

        with redirect_stdout(sys.stderr):
            recording = load(
                InputDataStep.get_recording_json_path(
                    self.output_path, self.session_name, self.shank_id
                )
            )

        spikeinterface_kwargs = copy.deepcopy(self.config["preprocessing"])
        save_preprocessed_copy = spikeinterface_kwargs.pop(
            "save_preprocessed_copy", False
        )

        pipeline = self._convert_kwargs_to_spikeinterface_pipeline(
            spikeinterface_kwargs, recording, verbose
        )

        with redirect_stdout(sys.stderr):
            preprocessed_rec = spre.apply_preprocessing_pipeline(
                recording, pipeline, apply_precomputed_kwargs=True
            )

        plot_preprocessing(
            recording,
            preprocessed_rec,
            step_path / "preprocessing_plots",
        )

        if save_preprocessed_copy:
            preprocessed_rec = preprocessed_rec.save(
                folder=step_path / "recording", verbose=verbose
            )

        preprocessed_rec.dump_to_json(
            step_path / "metadata.json", include_properties=True
        )

    def _convert_kwargs_to_spikeinterface_pipeline(
        self, spikeinterface_kwargs, recording, verbose
    ):
        """Load step inputs and convert kwargs to SpikeInterface's ordered list."""
        pipeline = []
        for step, kwargs in spikeinterface_kwargs.items():
            if step in ("remove_bad_channels", "interpolate_bad_channels"):
                bad_channel_ids = load_and_check_bad_channel_ids(
                    self.output_path,
                    self.config,
                    self.session_name,
                    self.shank_id,
                    required=True,
                    verbose=verbose,
                )
                if len(bad_channel_ids) == 0:
                    continue
                else:
                    kwargs["bad_channel_ids"] = bad_channel_ids

                # Convert to SpikeInterface pipeline name
                if step == "remove_bad_channels":
                    step = "detect_and_remove_bad_channels"

            elif step == "silence_periods":
                kwargs["periods"] = load_and_check_artefact_periods(
                    self.output_path,
                    self.session_name,
                    self.shank_id,
                    recording,
                    verbose=verbose,
                )
            pipeline.append({"name": step, "params": kwargs})

        return pipeline

    # ----------------------------------------------------------------------------------
    # Checks
    # ----------------------------------------------------------------------------------

    def perform_checks(self) -> None:
        """Check preprocessing inputs and operation order."""
        # Check mutually exclusive bad channel handling steps
        if {"remove_bad_channels", "interpolate_bad_channels"} <= self.config[
            "preprocessing"
        ].keys():
            raise ValueError(
                "Cannot configure both bad-channel removal and interpolation."
            )

        # Check preprocessing steps are in a sensible order
        self._check_operation_order()

        if (
            "bad_channel_detection" in self.config
            and "combine_sessions" in self.config
            and not {
                "remove_bad_channels",
                "interpolate_bad_channels",
            }
            & self.config["preprocessing"].keys()
        ):
            raise ValueError(
                "The config combines sessions with bad-channel detection, but "
                "preprocessing "
                "does not include remove_bad_channels or interpolate_bad_channels. "
                "Add either step to handle the union bad channels."
            )

    def _check_operation_order(self) -> None:
        """Check the configured order without rearranging any operations."""
        user_operations = list(self.config["preprocessing"])

        user_filter_steps = [
            name for name in TEMPORAL_FILTERS if name in user_operations
        ]
        user_referencing_steps = [
            name for name in SPATIAL_OPERATIONS if name in user_operations
        ]

        if "remove_bad_channels" in user_operations and not self._is_before(
            "remove_bad_channels", user_filter_steps + user_referencing_steps
        ):
            raise ValueError(
                "remove_bad_channels must precede filtering and referencing steps."
            )

        for operation in ("interpolate_bad_channels", "silence_periods"):
            if operation in user_operations:
                for temporal_filter in user_filter_steps:
                    if not self._is_before(temporal_filter, [operation]):
                        raise ValueError(
                            f"The {operation} step must be after {temporal_filter}."
                        )

        for operation in ("interpolate_bad_channels", "phase_shift"):
            if operation in user_operations and not self._is_before(
                operation, user_referencing_steps
            ):
                raise ValueError(
                    f"{operation} must precede reference steps and spatial filtering."
                )

    def _is_before(self, lhs: str, rhs: list[str]) -> bool:
        """Return whether lhs precedes every operation in rhs.

        The caller supplies configured operations only. An empty rhs returns True.
        """
        user_operations = list(self.config["preprocessing"])
        lhs_index = user_operations.index(lhs)
        return all(lhs_index < user_operations.index(operation) for operation in rhs)

    def needs_gpu(self) -> bool:
        """Report whether preprocessing requires a GPU."""
        return False
