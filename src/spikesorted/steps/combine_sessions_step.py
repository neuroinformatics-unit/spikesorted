"""Combine sessions step: join one shank's preprocessed sessions for sorting."""

from __future__ import annotations

import sys
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import spikeinterface as si
from spikeinterface import load

from spikesorted.plotting.combine_sessions import plot_concatenation_points
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
    order of ``session_names``. ``concatenate`` is the only method the
    config's ``combine_sessions`` section accepts.

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

    ``concatenation_plots/``
        A one-second trace image across each join between sessions, with the
        boundary marked.

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

    combined_session_name: ClassVar[str] = "combined-sessions"

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
            output_path, cls._step_name, cls.combined_session_name, shank_id
        )

    def run(self, verbose: bool = True) -> None:
        """Plot session boundaries and optionally save the combined recording.

        Parameters
        ----------
        verbose
            Whether to print progress messages.
        """
        step_path = self.get_output_path(self.output_path, self.shank_id)

        step_path.mkdir(parents=True, exist_ok=True)

        shank_message = f", shank {self.shank_id}" if self.shank_id else ""
        message_user(f"Concatenating sessions{shank_message}", verbose)

        session_preprocessing_paths = self.get_input_paths(
            self.output_path, self.session_names, self.shank_id
        )
        sessions = []
        with redirect_stdout(sys.stderr):
            for session_name, session_preprocessing_path in zip(
                self.session_names, session_preprocessing_paths, strict=True
            ):
                sessions.append(
                    (session_name, load(session_preprocessing_path / "metadata.json"))
                )

        # For now, concatenation is the only option and it is validated on load.
        combined = si.concatenate_recordings([recording for _, recording in sessions])
        plot_concatenation_points(combined, sessions, step_path / "concatenation_plots")

        if self.config["combine_sessions"].get("save_preprocessed_copy", False):
            combined = combined.save(folder=step_path / "recording", verbose=verbose)

        combined.dump_to_json(step_path / "metadata.json", include_properties=True)
