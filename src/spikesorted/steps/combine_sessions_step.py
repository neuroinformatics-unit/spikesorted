"""Combine sessions step: join one shank's preprocessed sessions for sorting."""

from __future__ import annotations

import sys
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from spikeinterface import concatenate_recordings, load

from spikesorted.steps.preprocessing_step import PreprocessingStep
from spikesorted.utils.output_paths import get_step_output_path
from spikesorted.utils.utils import load_pipeline_config, message_user

if TYPE_CHECKING:
    from spikesorted.validation.config_validation import PipelineConfig


@dataclass(frozen=True)
class CombineSessionsStep:
    """Concatenate one shank's preprocessed sessions into a single recording.

    Use this to sort several sessions together. It loads each session's
    preprocessed recording for the shank and joins them end to end, in the
    order of ``session_names``. Only the ``concatenate`` method of the
    config's ``combine_sessions`` section is supported.

    Outputs use "combined-sessions" as the session name.

    Parameters
    ----------
    session_names
        The sessions to combine, in the order they are joined.

    shank_id
        ID of the shank to combine.

    config_path
        Path to the YAML pipeline configuration file containing the
        ``combine_sessions`` settings.

    output_path
        The subject folder containing each session's preprocessing outputs.

    See Also
    --------
    spikeinterface.core.concatenate_recordings

    Notes
    -----
    The following are saved for the shank:

    ``recording/``
        The combined preprocessed data, saved when ``save_preprocessed_copy``
        in the config's ``combine_sessions`` section is true.

    ``metadata.json``
        A SpikeInterface JSON dump that later steps load the combined
        recording from. When ``recording/`` is saved it points at that.
        Otherwise it points at each session's preprocessed copy when the
        ``preprocessing`` step saved one, or at each session's raw data, with
        the preprocessing recomputed on loading.

    Examples
    --------
    >>> CombineSessionsStep(
    ...     session_names=("ses-001", "ses-002"),
    ...     shank_id="0",
    ...     config_path="config.yaml",
    ...     output_path="/derivatives/sub-001",
    ... ).run()
    """

    session_names: tuple[str, ...]
    shank_id: str
    config_path: str | Path
    output_path: str | Path

    _step_name: ClassVar[str] = "combine_sessions"

    _combined_session_name: ClassVar[str] = "combined-sessions"

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
        session_names: tuple[str, ...],
        shank_id: str,
    ) -> list[Path]:
        """Return each session's preprocessing folder for a shank.

        Parameters
        ----------
        output_path
            The subject folder.
        session_names
            The sessions to combine.
        shank_id
            Shank ID.

        Returns
        -------
        session_preprocessing_paths
            One preprocessing folder per session.
        """
        session_preprocessing_paths = []
        for session_name in session_names:
            session_preprocessing_paths.append(
                PreprocessingStep.get_output_path(output_path, session_name, shank_id)
            )
        return session_preprocessing_paths

    @classmethod
    def get_output_path(cls, output_path: str | Path, shank_id: str) -> Path:
        """Return the folder a shank's combined recording is written to.

        Parameters
        ----------
        output_path
            The subject folder.
        shank_id
            Shank ID.

        Returns
        -------
        step_path
            The shank's combine sessions folder.
        """
        return get_step_output_path(
            output_path, cls._step_name, cls._combined_session_name, shank_id
        )

    def run(self, verbose: bool = True) -> None:
        """Concatenate the sessions and save the metadata and optional copy.

        Parameters
        ----------
        verbose
            Whether to print progress messages.
        """
        combine_method = self.config["combine_sessions"]["method"]
        if combine_method != "concatenate":
            raise NotImplementedError(
                f"combine_sessions method {combine_method!r} is not supported. "
                "Use 'concatenate'."
            )

        step_path = self.get_output_path(self.output_path, self.shank_id)
        shank_message = f", shank {self.shank_id}" if self.shank_id else ""
        message_user(
            f"Combining sessions {list(self.session_names)}{shank_message}",
            verbose,
        )

        step_path.mkdir(parents=True, exist_ok=True)

        session_recordings = []
        with redirect_stdout(sys.stderr):
            for session_preprocessing_path in self.get_input_paths(
                self.output_path, self.session_names, self.shank_id
            ):
                session_recordings.append(
                    load(session_preprocessing_path / "metadata.json")
                )

            combined_recording = concatenate_recordings(session_recordings)

        if self.config["combine_sessions"].get("save_preprocessed_copy", False):
            combined_recording = combined_recording.save(
                folder=step_path / "recording", verbose=verbose
            )

        combined_recording.dump_to_json(
            step_path / "metadata.json", include_properties=True
        )

        message_user(
            f"Combined sessions saved to: {step_path}",
            verbose,
        )

    def needs_gpu(self) -> bool:
        """Report whether combining sessions requires a GPU."""
        return False
