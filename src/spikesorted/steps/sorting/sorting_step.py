"""Spike sorting step."""

import shutil
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from typing import ClassVar

from spikeinterface.sorters import run_sorter

from spikesorted.steps.base import BasePipelineStep
from spikesorted.steps.sorting.sorter_installation import ensure_kilosort_installed


@dataclass(frozen=True)
class SortingStep(BasePipelineStep):
    """Sort preprocessed recordings supplied as recording objects or saved paths."""

    _step_name: ClassVar[str] = "sorting"

    def run(self, verbose: bool = True) -> None:
        """Run the configured sorter and retain SpikeInterface's output files."""
        self.perform_checks()

        for _, _, recording, step_path in self._get_recordings_and_paths():
            with redirect_stdout(sys.stderr):
                run_sorter(
                    sorter_name=self.config["sorting"]["sorter"],
                    recording=recording,
                    folder=step_path,
                    verbose=verbose,
                    **self.config["sorting"].get("params", {}),
                )

    def perform_checks(self) -> None:
        """Check recordings, preprocessing compatibility, and existing outputs."""
        super().perform_checks()
        self._check_preprocessing_config()

        if not self.overwrite:
            for _, _, _, step_path in self._get_recordings_and_paths():
                if step_path.exists():
                    raise FileExistsError(
                        f"Sorting output already exists: {step_path}. "
                        "Set overwrite=True to replace existing outputs, "
                        "or choose a different output_path."
                    )

        sorter_name = self.config["sorting"]["sorter"]
        if sorter_name in ("kilosort2_5", "kilosort3"):
            ensure_kilosort_installed(sorter_name)

        for _, _, _, step_path in self._get_recordings_and_paths():
            if step_path.exists():
                shutil.rmtree(step_path)

    def needs_gpu(self) -> bool:
        """Report whether the configured sorter is Kilosort."""
        return self.config["sorting"]["sorter"].startswith("kilosort")

    def _check_preprocessing_config(self) -> None:
        """Check for duplicated preprocessing between the pipeline and sorter."""
        # TODO: Check filtering, referencing, whitening, and motion correction
        # against the selected sorter's effective parameters, including defaults.
        pass
