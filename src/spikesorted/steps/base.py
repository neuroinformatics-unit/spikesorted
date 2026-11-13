from __future__ import annotations

import sys
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from spikeinterface import load
from spikeinterface.core import BaseRecording

from spikesorted.utils.recordings_structure import get_recordings
from spikesorted.utils.utils import load_pipeline_config
from spikesorted.validation.steps_validation import _BaseStepArguments

if TYPE_CHECKING:
    from spikesorted.utils.recordings_structure import RecordingInput
    from spikesorted.validation.config_validation import PipelineConfig


@dataclass(frozen=True)
class BasePipelineStep:
    """The base PipelineStep that defines methods and sets up shared attributes.

    A frozen dataclass is used, to ensure attributes cannot easily be mutated.

    Parameters
    ----------
    recordings
        A RecordingsInput (either a recording, (recording, str), or {str: recording}
        object, or list thereof).
    config_path
        The path to a YAML PipelineConfig.
    output_path
        The output path for the pipeline step. Outputs for every
        session / shank in RecordingsInput will be saved here.
    overwrite
        If `True`, existing outputs found in `output_path`
        will be deleted and overwritten.

    """

    recordings: RecordingInput | list[RecordingInput]
    config_path: str | Path
    output_path: str | Path
    overwrite: bool = False

    _step_name: ClassVar[str]

    _highpass_freq_min: ClassVar[float] = 300

    _config: PipelineConfig = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Validate all attributes and store loaded / computed attributes."""
        _BaseStepArguments.model_validate(
            {
                "recordings": self.recordings,
                "config_path": self.config_path,
                "output_path": self.output_path,
                "overwrite": self.overwrite,
            }
        )
        loaded_config = load_pipeline_config(self.config_path)
        object.__setattr__(self, "_config", loaded_config)

    @property
    def config(self) -> PipelineConfig:
        """Return the dictionary loaded at construction, without rereading disk."""
        return self._config

    def perform_checks(self) -> None:
        """Check that every recording contains exactly one segment."""
        for session_name, shank_id, recording, _ in self._get_recordings_and_paths():
            if recording.get_num_segments() != 1:
                raise ValueError(
                    f"Only single-segment recordings are supported; "
                    f"session {session_name}, shank {shank_id} has "
                    f"{recording.get_num_segments()} segments."
                )

    def run(self, verbose: bool = True) -> None:
        """Perform checks, execute the step, and save its outputs."""
        raise NotImplementedError

    def needs_gpu(self) -> bool:
        """Report whether the configured operation requires a GPU."""
        raise NotImplementedError

    def get_first_recording(self) -> BaseRecording:
        """Return the first loaded recording from session/shank containers."""
        recording = self.recordings

        while not isinstance(recording, BaseRecording):
            if isinstance(recording, (list, tuple)):
                if not recording:
                    raise ValueError("At least one recording is required")
                recording = recording[0]

            elif isinstance(recording, dict):
                if not recording:
                    raise ValueError("At least one recording is required")
                recording = next(iter(recording.values()))

            elif isinstance(recording, (str, Path)):
                with redirect_stdout(sys.stderr):
                    recording = load(recording)

            else:
                raise TypeError("Load recording paths before accessing a recording")

        return recording

    def _get_output_path(
        self,
        session_name: str,
        shank_id: str | int | None = None,
    ) -> Path:
        """Return this step's output directory using the configured layout."""
        structure = self.config.get("output", {}).get("structure", "neuroblueprint")
        shank = () if shank_id is None else (f"shank_{shank_id}",)
        layouts = {
            "neuroblueprint": (session_name, "ephys", *shank, self._step_name),
            "by_session": (session_name, self._step_name, *shank),
            "by_step": (self._step_name, session_name, *shank),
        }
        return Path(self.output_path).joinpath(*layouts[structure])

    def _get_recordings_and_paths(
        self,
    ) -> list[tuple[str, str | int | None, BaseRecording, Path]]:
        """Pair each named recording with this step's output path."""
        return [
            (
                session_name,
                shank_id,
                recording,
                self._get_output_path(session_name, shank_id),
            )
            for session_name, shank_id, recording in get_recordings(self.recordings)
        ]
