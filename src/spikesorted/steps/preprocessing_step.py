"""Preprocess recordings using SpikeInterface's ordered pipeline."""

from __future__ import annotations

import copy
import shutil
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from typing import ClassVar

import spikeinterface.preprocessing as spre

from spikesorted.plotting.preprocessing import plot_preprocessing
from spikesorted.step_configs import (
    SPATIAL_OPERATIONS,
    TEMPORAL_FILTERS,
)
from spikesorted.steps.artifact_detection.utils import load_and_check_artefact_periods
from spikesorted.steps.bad_channel_detection.utils import (
    load_and_check_bad_channel_ids,
    get_bad_channel_ids_filepath,
)
from spikesorted.steps.base import BasePipelineStep
from spikesorted.utils.output_paths import get_step_output_path
from spikesorted.utils.recordings_structure import RecordingInput
from spikesorted.utils.utils import message_user


@dataclass(frozen=True)
class PreprocessingStep(BasePipelineStep):
    """Preprocess each session and shank using the configured operation order."""

    save_preprocessed_copy: bool = True

    _step_name: ClassVar[str] = "preprocessing"

    def run(self, verbose: bool = True) -> list[RecordingInput]:
        """Return named sessions containing saved paths or in-memory recordings."""
        self.perform_checks()

        processed_sessions = []

        for (
            session_name,
            shank_id,
            recording,
            step_path,
        ) in self._get_recordings_and_paths():
            shank_message = f", shank {shank_id}" if shank_id is not None else ""
            message_user(
                f"Preprocessing session {session_name}{shank_message}",
                verbose,
            )

            spikeinterface_kwargs = copy.deepcopy(self.config["preprocessing"])

            pipeline = self._convert_kwargs_to_spikeinterface_pipeline(
                spikeinterface_kwargs, session_name, shank_id, recording, verbose
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

            if self.save_preprocessed_copy:
                preprocessed_rec = preprocessed_rec.save(
                    folder=step_path / "recording", verbose=verbose
                )

            preprocessed_rec.dump_to_json(
                step_path / "metadata.json", include_properties=True
            )

            # Handover the path for the next step if recording
            # is saved to disk, otherwise the recording in-memory
            if self.save_preprocessed_copy:
                processed_output = step_path / "recording"
            else:
                processed_output = preprocessed_rec

            # Store each session as one recording/path or a dictionary of shanks.
            if shank_id is None:
                processed_sessions.append((processed_output, session_name))
            else:
                if processed_sessions and processed_sessions[-1][1] == session_name:
                    processed_sessions[-1][0][shank_id] = processed_output
                else:
                    processed_sessions.append(
                        ({shank_id: processed_output}, session_name)
                    )

        return processed_sessions

    def _convert_kwargs_to_spikeinterface_pipeline(
        self, spikeinterface_kwargs, session_name, shank_id, recording, verbose
    ):
        """Load step inputs and convert kwargs to SpikeInterface's ordered list."""
        pipeline = []
        for step, kwargs in spikeinterface_kwargs.items():
            if step in ("remove_bad_channels", "interpolate_bad_channels"):
                bad_channel_ids = load_and_check_bad_channel_ids(
                    self.output_path,
                    self.config,
                    session_name,
                    shank_id,
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
                    self.config,
                    session_name,
                    shank_id,
                    recording,
                    verbose=verbose,
                )
            pipeline.append({"name": step, "params": kwargs})

        return pipeline

    # ----------------------------------------------------------------------------------
    # Checks
    # ----------------------------------------------------------------------------------

    def perform_checks(self) -> None:
        """Check preprocessing inputs and operation order.
        """
        # Check mutually exclusive bad channel handling steps
        if {"remove_bad_channels", "interpolate_bad_channels"} <= self.config[
            "preprocessing"
        ].keys():
            raise ValueError(
                "Cannot configure both bad-channel removal and interpolation."
            )

        # Check preprocessing steps are in a sensible order
        self._check_operation_order()

        # Check overwrite settings and
        for _, shank_id, _, step_path in self._get_recordings_and_paths():

            if step_path.exists() and not self.overwrite:
                raise FileExistsError(
                    f"Preprocessing output already exists: {step_path}"
                )
            union_path = get_bad_channel_ids_filepath(
                get_step_output_path(
                    self.output_path,
                    self.config,
                    "bad_channel_detection",
                    "session_unions",
                    shank_id,
                )
            )
            if (
                union_path.is_file()
                and not {
                    "remove_bad_channels",
                    "interpolate_bad_channels",
                } & self.config["preprocessing"].keys()
            ):
                raise ValueError(
                    f"Bad-channel union exists at {union_path}, but preprocessing "
                    "does not include remove_bad_channels or interpolate_bad_channels. "
                    "Add either step to handle the union bad channels."
                )

        # Check overwrite settings, and delete existing outputs
        super().perform_checks()

        for _, _, _, step_path in self._get_recordings_and_paths():
            if step_path.exists():
                shutil.rmtree(step_path)

            step_path.mkdir(parents=True)

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
