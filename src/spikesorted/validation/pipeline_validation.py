"""Validation of pipeline constructor arguments."""

from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from spikesorted.utils.recordings_structure import RecordingInput

PIPELINE_STEP_NAMES = (
    "bad_channel_detection",
    "raw_data_quality_metrics",
    "artifact_detection",
)


class _PipelineArguments(BaseModel):
    """Validate pipeline inputs without loading or inspecting recording data."""

    model_config = ConfigDict(strict=True, arbitrary_types_allowed=True)

    recordings: RecordingInput | list[RecordingInput]
    config_path: str | Path
    output_path: str | Path
    start_at_step: (
        Literal[
            "bad_channel_detection", "raw_data_quality_metrics", "artifact_detection"
        ]
        | None
    )
    stop_after_step: (
        Literal[
            "bad_channel_detection", "raw_data_quality_metrics", "artifact_detection"
        ]
        | None
    )
    overwrite: bool
    n_jobs: int
    verbose: bool

    @field_validator("n_jobs")
    @classmethod
    def validate_n_jobs(cls, value: int) -> int:
        """Require a nonzero integer, preserving SI's negative worker counts."""
        if value == 0:
            raise ValueError("n_jobs must be a nonzero integer.")
        return value

    @model_validator(mode="after")
    def validate_step_order(self) -> Self:
        """Require execution boundaries in pipeline order."""
        if self.start_at_step is not None and self.stop_after_step is not None:
            if PIPELINE_STEP_NAMES.index(
                self.start_at_step
            ) > PIPELINE_STEP_NAMES.index(self.stop_after_step):
                raise ValueError("start_at_step must not come after stop_after_step.")
        return self
