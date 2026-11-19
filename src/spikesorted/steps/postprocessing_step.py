"""Postprocess saved sortings with their matching preprocessed recordings."""

import copy
import shutil
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from typing import ClassVar

from spikeinterface.full import (
    create_sorting_analyzer,
    get_quality_metric_list,
    read_sorter_folder,
)

from spikesorted.steps.base import BasePipelineStep
from spikesorted.utils.output_paths import get_step_output_path


@dataclass(frozen=True)
class PostprocessingStep(BasePipelineStep):
    """Save an analyzer and quality metrics for each session and shank."""

    _step_name: ClassVar[str] = "postprocessing"

    def run(self, verbose: bool = True) -> None:
        """Compute configured extensions and export per-unit quality metrics."""
        self.perform_checks()

        for (
            session_name,
            shank_id,
            recording,
            step_path,
        ) in self._get_recordings_and_paths():

            sorting_path = get_step_output_path(
                self.output_path, self.config, "sorting", session_name, shank_id
            )

            extensions = copy.deepcopy(self.config["postprocessing"])
            sparsity_kwargs = extensions.pop("compute_sparsity", None)
            quality_metrics_kwargs = extensions.pop("quality_metrics")

            if quality_metrics_kwargs.get("metric_names") == "all":
                quality_metrics_kwargs["metric_names"] = get_quality_metric_list()

            with redirect_stdout(sys.stderr):

                sorting = read_sorter_folder(sorting_path, register_recording=False)

                analyzer = create_sorting_analyzer(
                    sorting=sorting,
                    recording=recording,
                    format="binary_folder",
                    folder=step_path / "sorting_analyzer",
                    sparsity_kwargs=sparsity_kwargs,
                )
                analyzer.compute(extensions, verbose=verbose)
                analyzer.compute(
                    "quality_metrics", verbose=verbose, **quality_metrics_kwargs
                )

            analyzer.get_extension("quality_metrics").get_data().to_csv(
                step_path / "quality_metrics.csv", index_label="unit_id"
            )

    def perform_checks(self) -> None:
        """Check recordings and handle existing postprocessing outputs upfront."""
        super().perform_checks()

        if not self.overwrite:
            for _, _, _, step_path in self._get_recordings_and_paths():
                if step_path.exists():
                    raise FileExistsError(
                        f"Postprocessing output already exists: {step_path}. "
                        "Set overwrite=True to replace existing outputs, "
                        "or choose a different output_path."
                    )

        for _, _, _, step_path in self._get_recordings_and_paths():
            if step_path.exists():
                shutil.rmtree(step_path)

    def needs_gpu(self) -> bool:
        """Report whether postprocessing requires a GPU."""
        return False
