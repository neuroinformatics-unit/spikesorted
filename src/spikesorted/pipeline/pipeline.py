"""Pipeline orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import spikeinterface as si

from spikesorted.steps.artifact_detection import ArtifactDetectionStep
from spikesorted.steps.bad_channel_detection import BadChannelDetectionStep
from spikesorted.steps.postprocessing_step import PostprocessingStep
from spikesorted.steps.preprocessing_step import PreprocessingStep
from spikesorted.steps.raw_data_quality_metrics_step import RawDataQualityMetricsStep
from spikesorted.steps.sorting import SortingStep
from spikesorted.utils.recordings_structure import check_and_normalize_recordings
from spikesorted.utils.utils import load_pipeline_config
from spikesorted.validation.pipeline_validation import _PipelineArguments

if TYPE_CHECKING:
    from spikesorted.utils.recordings_structure import RecordingInput


class Pipeline:
    """Electrophysiology analysis pipeline."""

    def __init__(
        self,
        recordings: RecordingInput | list[RecordingInput],
        config_path: str | Path,
        output_path: str | Path,
        start_at_step: str | None = None,
        stop_after_step: str | None = None,
        overwrite: bool = False,
        n_jobs: int = 1,
        verbose: bool = True,
        save_preprocessed_copy: bool = True,
    ) -> None:
        """Store recordings, configuration path, output root, and execution options."""
        _PipelineArguments.model_validate(
            {
                "recordings": recordings,
                "config_path": config_path,
                "output_path": output_path,
                "start_at_step": start_at_step,
                "stop_after_step": stop_after_step,
                "overwrite": overwrite,
                "n_jobs": n_jobs,
                "verbose": verbose,
                "save_preprocessed_copy": save_preprocessed_copy,
            }
        )
        self.recordings = check_and_normalize_recordings(recordings)
        self.config_path = config_path
        self.output_path = output_path
        self.start_at_step = start_at_step
        self.stop_after_step = stop_after_step
        self.overwrite = overwrite
        self.n_jobs = n_jobs
        self.verbose = verbose
        self.save_preprocessed_copy = save_preprocessed_copy

    def run(self) -> None:  # noqa: C901 - Keep the pipeline step sequence explicit.
        """Run selected steps; sorting/postprocessing inputs must be preprocessed."""
        si.set_global_job_kwargs(n_jobs=self.n_jobs)
        configs = load_pipeline_config(self.config_path)
        recordings = self.recordings

        if "bad_channel_detection" in configs and self.start_at_step in [
            None,
            "bad_channel_detection",
        ]:
            bad_channel_detection = BadChannelDetectionStep(
                recordings=self.recordings,
                config_path=self.config_path,
                output_path=self.output_path,
                overwrite=self.overwrite,
            )
            bad_channel_detection.run(self.verbose)

        if self.stop_after_step == "bad_channel_detection":
            return

        if "raw_data_quality_metrics" in configs and self.start_at_step in [
            None,
            "bad_channel_detection",
            "raw_data_quality_metrics",
        ]:
            raw_data_quality_metrics = RawDataQualityMetricsStep(
                recordings=self.recordings,
                config_path=self.config_path,
                output_path=self.output_path,
                overwrite=self.overwrite,
            )
            raw_data_quality_metrics.run(self.verbose)

        if self.stop_after_step == "raw_data_quality_metrics":
            return

        if "artifact_detection" in configs and self.start_at_step in [
            None,
            "bad_channel_detection",
            "raw_data_quality_metrics",
            "artifact_detection",
        ]:
            artifact_detection = ArtifactDetectionStep(
                recordings=self.recordings,
                config_path=self.config_path,
                output_path=self.output_path,
                overwrite=self.overwrite,
            )
            artifact_detection.run(self.verbose)

        if self.stop_after_step == "artifact_detection":
            return

        if "preprocessing" in configs and self.start_at_step in [
            None,
            "bad_channel_detection",
            "raw_data_quality_metrics",
            "artifact_detection",
            "preprocessing",
        ]:
            preprocessing = PreprocessingStep(
                save_preprocessed_copy=self.save_preprocessed_copy,
                recordings=self.recordings,
                config_path=self.config_path,
                output_path=self.output_path,
                overwrite=self.overwrite,
            )
            recordings = preprocessing.run(self.verbose)

        if self.stop_after_step == "preprocessing":
            return

        if "sorting" in configs and self.start_at_step in [
            None,
            "bad_channel_detection",
            "raw_data_quality_metrics",
            "artifact_detection",
            "preprocessing",
            "sorting",
        ]:
            sorting = SortingStep(
                recordings=recordings,
                config_path=self.config_path,
                output_path=self.output_path,
                overwrite=self.overwrite,
            )
            sorting.run(self.verbose)

        if self.stop_after_step == "sorting":
            return

        if "postprocessing" in configs and self.start_at_step in [
            None,
            "bad_channel_detection",
            "raw_data_quality_metrics",
            "artifact_detection",
            "preprocessing",
            "sorting",
            "postprocessing",
        ]:
            postprocessing = PostprocessingStep(
                recordings=recordings,
                config_path=self.config_path,
                output_path=self.output_path,
                overwrite=self.overwrite,
            )
            postprocessing.run(self.verbose)

        return None
