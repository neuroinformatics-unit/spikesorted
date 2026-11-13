"""Pipeline orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import spikeinterface as si

from spikesorted.steps.artifact_detection import ArtifactDetectionStep
from spikesorted.steps.bad_channel_detection import BadChannelDetectionStep
from spikesorted.steps.raw_data_quality_metrics import RawDataQualityMetricsStep
from spikesorted.utils.utils import load_pipeline_config
from spikesorted.validation.pipeline_validation import validate_pipeline_steps

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
    ) -> None:
        """Store recordings, configuration path, output root, and execution options."""
        self.recordings = recordings
        self.config_path = config_path
        self.output_path = output_path
        self.start_at_step = start_at_step
        self.stop_after_step = stop_after_step
        self.overwrite = overwrite
        self.n_jobs = n_jobs
        self.verbose = verbose

    def run(self) -> None:
        """Run from start_at_step, stopping after stop_after_step executes."""
        si.set_global_job_kwargs(n_jobs=self.n_jobs)
        configs = load_pipeline_config(self.config_path)
        validate_pipeline_steps(self.start_at_step, self.stop_after_step)

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
