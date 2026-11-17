"""Preprocess recordings using SpikeInterface's ordered pipeline."""

from __future__ import annotations

import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

import numpy as np
import spikeinterface.preprocessing as spre
from spikeinterface.core.base import base_period_dtype

from spikesorted.step_configs import SPATIAL_OPERATIONS, TEMPORAL_FILTERS
from spikesorted.steps.artifact_detection import ArtifactDetectionStep
from spikesorted.steps.bad_channel_detection import BadChannelDetectionStep
from spikesorted.steps.base import BasePipelineStep

if TYPE_CHECKING:
    from spikesorted.utils.recordings_structure import RecordingInput


@dataclass(frozen=True)
class PreprocessingStep(BasePipelineStep):
    """Preprocess each session and shank using the configured operation order."""

    _step_name: ClassVar[str] = "preprocessing"

    def perform_checks(self) -> None:
        """Check preprocessing inputs and operation order.

        - Require one segment per session/shank recording.
        - Reject simultaneous bad-channel removal and interpolation.
        - Require removal before filtering and referencing.
        - Require interpolation after temporal filtering and before referencing
          or spatial filtering.
        - Require phase shifting before referencing or spatial filtering.
        - Require silencing after temporal filtering.
        - Error if a union exists without combine_sessions, or combine_sessions
          is configured without the required union.

        Required detection files and artefact times are checked by the loaders
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
        bad_channel_detection = BadChannelDetectionStep(
            recordings=self.recordings,
            config_path=self.config_path,
            output_path=self.output_path,
        )

        for session_name, shank_id, recording, _ in self._get_recordings_and_paths():
            self._check_combine_sessions_bad_channels_union(
                bad_channel_detection, shank_id
            )

    def _check_combine_sessions_bad_channels_union(
        self, bad_channel_detection, shank_id
    ):
        """"""
        combine_sessions = "combine_sessions" in self.config

        union_path = bad_channel_detection.get_bad_channel_ids_filepath(
            bad_channel_detection._get_output_path("session_unions", shank_id)
        )

        if combine_sessions:
            if not union_path.is_file():
                raise FileNotFoundError(
                    f"combine_sessions requires a bad-channel union: {union_path}"
                )
        else:
            if union_path.is_file():
                raise ValueError(
                    "Bad-channel union exists but combine_sessions is not "
                    f"configured: {union_path}"
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
        """Return lazy recordings as named sessions, retaining their shank IDs."""
        self.perform_checks()

        processed_sessions = {}

        for session_name, shank_id, recording, _ in self._get_recordings_and_paths():
            if verbose:
                shank_message = f", shank {shank_id}" if shank_id is not None else ""
                print(
                    f"Preprocessing session {session_name}{shank_message}",
                    file=sys.stderr,
                    flush=True,
                )

            user_operations = {
                operation: kwargs.copy()
                for operation, kwargs in self.config["preprocessing"].items()
            }
            if "silence_periods" in user_operations:
                user_operations["silence_periods"]["periods"] = (
                    self._load_silence_periods(session_name, shank_id, recording)
                )

            for operation in ("remove_bad_channels", "interpolate_bad_channels"):
                if operation in user_operations:
                    bad_channel_ids = self._load_bad_channels(session_name, shank_id)
                    if len(bad_channel_ids) == 0:
                        del user_operations[operation]
                    else:
                        user_operations[operation]["bad_channel_ids"] = bad_channel_ids

            pipeline = []
            for operation, kwargs in user_operations.items():
                if operation == "remove_bad_channels":
                    operation = "detect_and_remove_bad_channels"
                pipeline.append({"name": operation, "params": kwargs})

            with redirect_stdout(sys.stderr):
                processed = spre.apply_preprocessing_pipeline(
                    recording, pipeline, apply_precomputed_kwargs=True
                )

            processed_sessions.setdefault(session_name, {})[shank_id] = processed

        recordings = []
        for session_name, shanks in processed_sessions.items():
            if None in shanks:
                recordings.append((shanks[None], session_name))
            else:
                recordings.append((shanks, session_name))

        return recordings

    def _load_bad_channels(self, session_name, shank_id):
        """Load the required session or union bad-channel IDs."""
        bad_channel_detection = BadChannelDetectionStep(
            recordings=self.recordings,
            config_path=self.config_path,
            output_path=self.output_path,
        )
        return bad_channel_detection.load_bad_channels(
            session_name,
            shank_id,
            combine_sessions="combine_sessions" in self.config,
            required=True,
        )

    def _load_silence_periods(self, session_name, shank_id, recording):
        """Load validated artefact periods in SpikeInterface's sample format."""
        artifact_detection = ArtifactDetectionStep(
            recordings=self.recordings,
            config_path=self.config_path,
            output_path=self.output_path,
        )
        periods = artifact_detection.load_artifacts_against_recording(
            session_name, shank_id, recording
        )
        si_periods = np.zeros(len(periods), dtype=base_period_dtype)
        for column in ("start_sample_index", "end_sample_index"):
            si_periods[column] = periods[column].to_numpy()
        return si_periods
