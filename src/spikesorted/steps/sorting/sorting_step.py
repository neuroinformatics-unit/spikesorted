"""Spike sorting step for one session shank, or one shank's combined sessions."""

from __future__ import annotations

import sys
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from spikeinterface import load
from spikeinterface.sorters import run_sorter

from spikesorted.steps.combine_sessions_step import CombineSessionsStep
from spikesorted.steps.preprocessing_step import PreprocessingStep
from spikesorted.steps.sorting.sorter_installation import register_installed_kilosort
from spikesorted.utils.output_paths import get_step_output_path
from spikesorted.utils.utils import load_pipeline_config

if TYPE_CHECKING:
    from spikesorted.validation.config_validation import PipelineConfig


@dataclass(frozen=True)
class SortingStep:
    """Sort one preprocessed recording with the configured sorter.

    The ``run()`` method wraps SpikeInterface's ``run_sorter()``. Without
    ``combine_sessions`` in the config it sorts one session shank's
    preprocessed recording. With ``combine_sessions`` it sorts one shank's
    combined recording.

    Parameters
    ----------
    session_name
        Name of the session to sort. With ``combine_sessions`` in the config,
        pass ``CombineSessionsStep.combined_session_name``.

    shank_id
        ID of the shank to sort.

    config_path
        Path to the YAML pipeline configuration file containing the
        ``sorting`` settings.

    output_path
        The subject folder. The preprocessed recording is read from it, and
        the sorting output is written beside it.

    See Also
    --------
    spikeinterface.sorters.run_sorter

    Examples
    --------
    >>> SortingStep(
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

    _step_name: ClassVar[str] = "sorting"

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
        """Return the folder this step waits for, for a session shank.

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
            The shank's combine sessions folder when the config includes
            ``combine_sessions``, otherwise the session shank's preprocessing
            folder.
        """
        if "combine_sessions" in config:
            return [CombineSessionsStep.get_output_path(output_path, shank_id)]
        else:
            return [
                PreprocessingStep.get_output_path(output_path, session_name, shank_id)
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
            The session shank's sorting folder.
        """
        return get_step_output_path(output_path, cls._step_name, session_name, shank_id)

    def run(self, verbose: bool = True) -> None:
        """Run the configured sorter and retain SpikeInterface's output files.

        Parameters
        ----------
        verbose
            Whether to print progress messages.
        """
        self.perform_checks()

        step_path = self.get_output_path(
            self.output_path, self.session_name, self.shank_id
        )
        (input_path,) = self.get_input_paths(
            self.output_path, self.config, self.session_name, self.shank_id
        )

        with redirect_stdout(sys.stderr):
            recording = load(input_path / "metadata.json")

            run_sorter(
                sorter_name=self.config["sorting"]["sorter"],
                recording=recording,
                folder=step_path,
                verbose=verbose,
                **self.config["sorting"].get("params", {}),
            )

    def perform_checks(self) -> None:
        """Check preprocessing compatibility and register MATLAB Kilosort."""
        self._check_preprocessing_config()

        sorter_name = self.config["sorting"]["sorter"]
        if sorter_name in ("kilosort2_5", "kilosort3"):
            register_installed_kilosort(sorter_name)

    def needs_gpu(self) -> bool:
        """Report whether the configured sorter is Kilosort."""
        return self.config["sorting"]["sorter"].startswith("kilosort")

    def _check_preprocessing_config(self) -> None:
        """Check for duplicated preprocessing between the pipeline and sorter."""
        # TODO: Check filtering, referencing, whitening, and motion correction
        # against the selected sorter's effective parameters, including defaults.
        pass
