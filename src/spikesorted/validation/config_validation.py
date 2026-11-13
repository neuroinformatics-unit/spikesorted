"""Validate pipeline configuration using SpikeInterface's declared parameters."""

from typing import Annotated, Any, Literal

from pydantic import AfterValidator, ConfigDict, TypeAdapter, with_config
from typing_extensions import TypedDict

from spikesorted.validation.steps_validation import (
    _validate_bad_channel_config,
    _validate_raw_data_quality_metrics_config,
)


@with_config(ConfigDict(extra="forbid", strict=True))
class OutputConfig(TypedDict, total=False):
    """Output folder layout; omitted structure uses NeuroBlueprint."""

    structure: Literal["neuroblueprint", "by_session", "by_step"]


@with_config(ConfigDict(extra="forbid", strict=True))
class PipelineConfig(TypedDict, total=False):
    """Optional pipeline sections; unimplemented sections accept any value."""

    bad_channel_detection: Annotated[
        dict[str, Any], AfterValidator(_validate_bad_channel_config)
    ]
    output: OutputConfig
    raw_data_quality_metrics: Annotated[
        dict[str, Any], AfterValidator(_validate_raw_data_quality_metrics_config)
    ]
    artifact_detection: Any
    artifact_curation: Any
    preprocessing: Any
    combine_sessions: Any
    sorting: Any
    postprocessing: Any
    curation: Any


_pipeline_config_adapter: TypeAdapter[PipelineConfig] = TypeAdapter(PipelineConfig)


def validate_config(config: object) -> PipelineConfig:
    """Return a validated dictionary without adding defaults or coercing values.

    Other allowed sections remain unchanged until their validators are implemented.
    Raw-data metric sampling options also require finite, valid ranges.
    Recording-dependent constraints remain SI's responsibility.
    """
    return _pipeline_config_adapter.validate_python(config)
