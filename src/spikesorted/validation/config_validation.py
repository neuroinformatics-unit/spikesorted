"""Validate pipeline configuration using SpikeInterface's declared parameters."""

from typing import Annotated, Any, Literal, NotRequired

from pydantic import AfterValidator, ConfigDict, TypeAdapter, with_config
from typing_extensions import TypedDict

from spikesorted.validation.steps_validation import (
    _validate_bad_channel_config,
    _validate_raw_data_quality_metrics_config,
)


@with_config(ConfigDict(extra="forbid", strict=True))
class CombineSessionsConfig(TypedDict):
    """Concatenate sessions, optionally saving the combined recording."""

    method: Literal["concatenate"]
    save_preprocessed_copy: NotRequired[bool]


@with_config(ConfigDict(extra="forbid", strict=True))
class PipelineConfig(TypedDict, total=False):
    """Optional pipeline sections; unimplemented sections accept any value."""

    bad_channel_detection: Annotated[
        dict[str, Any], AfterValidator(_validate_bad_channel_config)
    ]
    raw_data_quality_metrics: Annotated[
        dict[str, Any], AfterValidator(_validate_raw_data_quality_metrics_config)
    ]
    artifact_detection: Any
    artifact_curation: Any
    preprocessing: Any
    combine_sessions: CombineSessionsConfig
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
    validated_config = _pipeline_config_adapter.validate_python(config)

    if "preprocessing" not in validated_config:
        raise ValueError("The config must include a preprocessing section.")

    if "sorting" not in validated_config:
        raise ValueError("The config must include a sorting section.")

    # combine_sessions.save_preprocessed_copy is checked by CombineSessionsConfig.
    save_preprocessed_copy = validated_config["preprocessing"].get(
        "save_preprocessed_copy", False
    )
    if not isinstance(save_preprocessed_copy, bool):
        raise ValueError(
            "preprocessing.save_preprocessed_copy must be true or false, "
            f"not {save_preprocessed_copy!r}."
        )

    if (
        "preprocessing" in validated_config
        and "combine_sessions" in validated_config
        and validated_config["preprocessing"].get("save_preprocessed_copy", False)
        and validated_config["combine_sessions"].get("save_preprocessed_copy", False)
    ):
        raise ValueError(
            "save_preprocessed_copy cannot be true for both preprocessing and "
            "combine_sessions. Set it to true in only one of them."
        )
    return validated_config
