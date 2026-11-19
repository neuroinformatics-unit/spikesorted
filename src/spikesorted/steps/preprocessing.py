"""Preprocess recordings using SpikeInterface's ordered pipeline."""

from __future__ import annotations

import copy
import shutil
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import spikeinterface.preprocessing as spre

from spikesorted.plotting.preprocessing import plot_preprocessing
from spikesorted.step_configs import (
    SPATIAL_OPERATIONS,
    TEMPORAL_FILTERS,
    get_bad_channel_step,
)
from spikesorted.steps.artifact_detection.utils import artefact_period_loader
from spikesorted.steps.bad_channel_detection.utils import (
    bad_channel_id_loader,
    get_bad_channel_ids_filepath,
)
from spikesorted.steps.base import BasePipelineStep
from spikesorted.utils.output_paths import get_step_output_path
from spikesorted.utils.utils import message_user

if TYPE_CHECKING:
    from spikesorted.utils.recordings_structure import RecordingInput


@dataclass(frozen=True)
class PreprocessingStep(BasePipelineStep):
    """Preprocess each session and shank using the configured operation order."""

    save_preprocessed_copy: bool = True

    _step_name: ClassVar[str] = "preprocessing"

    def perform_checks(self) -> None:
        """Check preprocessing inputs and operation order.

        - Require one segment per session/shank recording.
        - Reject existing preprocessing output unless overwrite is enabled.
        - Prepare output folders, replacing existing ones when overwrite is enabled.
        - Reject simultaneous bad-channel removal and interpolation.
        - Require removal before filtering and referencing.
        - Require interpolation after temporal filtering and before referencing
          or spatial filtering.
        - Require phase shifting before referencing or spatial filtering.
        - Require silencing after temporal filtering.
        - Require explicit bad-channel removal when a union exists.

        Union/config consistency, required detection files and artefact times
        are checked by the loaders
        when the preprocessing inputs are loaded.
        """
        if {"remove_bad_channels", "interpolate_bad_channels"} <= self.config[
            "preprocessing"
        ].keys():
            raise ValueError(
                "Cannot configure both bad-channel removal and interpolation."
            )

        super().perform_checks()
        self._check_operation_order()

        # Check bad channel detection

        #     handle_bad_channels = (
        #         "remove_bad_channels" in preprocessing
        #         or "interpolate_bad_channels" in preprocessing
        #     )
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
                and "remove_bad_channels" not in self.config["preprocessing"]
            ):
                raise ValueError(
                    f"Bad-channel union exists at {union_path}, but preprocessing "
                    "does not include remove_bad_channels. Add explicit "
                    "remove_bad_channels; interpolation alone does not satisfy "
                    "the union requirement."
                )

        for _, _, _, step_path in self._get_recordings_and_paths():
            if step_path.exists():
                step_path.resolve().relative_to(Path(self.output_path).resolve())
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
                    f"{operation} must precede referncing steps and spatial filtering."
                )

    def _is_before(self, lhs: str, rhs: list[str]) -> bool:
        """Return whether lhs precedes every operation in rhs.

        The caller supplies configured operations only. An empty rhs returns True.
        """
        user_operations = list(self.config["preprocessing"])
        lhs_index = user_operations.index(lhs)
        return all(lhs_index < user_operations.index(operation) for operation in rhs)

    def run(self, verbose: bool = True) -> list[RecordingInput]:
        """Save outputs and return named recordings, retaining their shank IDs."""
        self.perform_checks()

        processed_sessions = {}

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

            self._load_artefact_periods_into_kwargs(
                spikeinterface_kwargs, session_name, shank_id, recording, verbose
            )
            self._load_bad_channels_into_kwargs(
                spikeinterface_kwargs, session_name, shank_id, verbose
            )

            pipeline = self._rename_steps_for_spikeinterface(spikeinterface_kwargs)

            with redirect_stdout(sys.stderr):
                processed = spre.apply_preprocessing_pipeline(
                    recording, pipeline, apply_precomputed_kwargs=True
                )

            plot_preprocessing(
                recording,
                processed,
                step_path / "preprocessing_plots",
            )

            if self.save_preprocessed_copy:
                processed = processed.save(
                    folder=step_path / "recording", verbose=verbose
                )
            else:
                processed.dump_to_json(
                    step_path / "metadata.json", include_properties=True
                )

            processed_sessions.setdefault(session_name, {})[shank_id] = processed

        recordings = []
        for session_name, shanks in processed_sessions.items():
            if None in shanks:
                recordings.append((shanks[None], session_name))
            else:
                recordings.append((shanks, session_name))

        return recordings

    def _load_bad_channels_into_kwargs(
        self, spikeinterface_kwargs, session_name, shank_id, verbose
    ):
        """Load bad-channel IDs into kwargs, skipping an empty bad-channel step."""
        handle_bad_channel_step = get_bad_channel_step(spikeinterface_kwargs)
        if handle_bad_channel_step is not None:
            # remove or interpolate
            bad_channel_ids = bad_channel_id_loader(
                self.output_path,
                self.config,
                session_name,
                shank_id,
                required=True,
                verbose=verbose,
            )
            if len(bad_channel_ids) == 0:
                del spikeinterface_kwargs[handle_bad_channel_step]
            else:
                spikeinterface_kwargs[handle_bad_channel_step]["bad_channel_ids"] = (
                    bad_channel_ids
                )

    def _load_artefact_periods_into_kwargs(
        self, spikeinterface_kwargs, session_name, shank_id, recording, verbose
    ):
        """Load validated artefact periods into the configured silencing step."""
        if "silence_periods" in spikeinterface_kwargs:
            spikeinterface_kwargs["silence_periods"]["periods"] = (
                artefact_period_loader(
                    self.output_path,
                    self.config,
                    session_name,
                    shank_id,
                    recording,
                    verbose=verbose,
                )
            )

    def _rename_steps_for_spikeinterface(self, spikeinterface_kwargs):
        """Translate the removal name and convert kwargs to SI's ordered list."""
        names = {
            "remove_bad_channels": "detect_and_remove_bad_channels",
        }
        pipeline = []
        for step, kwargs in spikeinterface_kwargs.items():
            if step in names:
                step = names[step]

            pipeline.append({"name": step, "params": kwargs})

        return pipeline
