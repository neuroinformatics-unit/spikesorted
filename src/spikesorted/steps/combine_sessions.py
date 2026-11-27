"""Concatenate sessions in input order, separately for each shank."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, cast

import spikeinterface as si

from spikesorted.plotting.combine_sessions import plot_concatenation_points
from spikesorted.steps.base import BasePipelineStep
from spikesorted.utils.recordings_structure import get_recordings
from spikesorted.utils.utils import message_user

if TYPE_CHECKING:
    from spikeinterface.core import BaseRecording

    from spikesorted.utils.recordings_structure import SessionRecording


@dataclass(frozen=True)
class CombineSessionsStep(BasePipelineStep):
    """Combine preprocessed sessions using concatenation."""

    _step_name: ClassVar[str] = "combine_sessions"

    def run(self, verbose: bool = True) -> list[tuple[SessionRecording, str]]:
        """Plot session boundaries and optionally save the combined recording."""
        self.perform_checks()

        shanks: dict[str | int | None, list[tuple[str, BaseRecording]]] = {}
        for session_name, shank_id, recording in get_recordings(
            cast("list[tuple[SessionRecording, str]]", self.recordings)
        ):
            shanks.setdefault(shank_id, []).append((session_name, recording))

        combined_shanks = {}
        for shank_id, sessions in shanks.items():
            step_path = self._get_output_path("combined_sessions", shank_id)

            step_path.mkdir(parents=True, exist_ok=False)

            shank_message = f", shank {shank_id}" if shank_id is not None else ""
            message_user(f"Concatenating sessions{shank_message}", verbose)

            # For now, concatenation is the only option and it is validated on load.
            combined = si.concatenate_recordings(
                [recording for _, recording in sessions]
            )
            plot_concatenation_points(
                combined, sessions, step_path / "concatenation_plots"
            )

            if self.config["combine_sessions"].get("save_recording", False):
                combined = combined.save(
                    folder=step_path / "recording", verbose=verbose
                )
            else:
                combined.dump_to_json(
                    step_path / "metadata.json", include_properties=True
                )

            combined_shanks[shank_id] = combined

        if None in combined_shanks:
            return [(combined_shanks[None], "combined_sessions")]
        else:
            return [(combined_shanks, "combined_sessions")]

    def perform_checks(self) -> None:
        """Check recording segments and existing combined-session outputs."""
        super().perform_checks()

        for _, shank_id, _ in get_recordings(
            cast("list[tuple[SessionRecording, str]]", self.recordings)
        ):
            step_path = self._get_output_path("combined_sessions", shank_id)
            if step_path.exists():
                if not self.overwrite:
                    raise FileExistsError(
                        f"Combined sessions output already exists: {step_path}"
                    )
                shutil.rmtree(step_path)
