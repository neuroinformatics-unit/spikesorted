"""Validation for shared step constructor arguments."""

from inspect import Parameter, signature
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field, create_model
from spikeinterface.preprocessing import detect_bad_channels
from spikeinterface.qualitycontrol import raw_data_quality_metrics

from spikesorted.utils.recordings_structure import RecordingInput


class _BaseStepArguments(BaseModel):
    """Validate shared constructor arguments without inspecting recording data."""

    model_config = ConfigDict(strict=True, arbitrary_types_allowed=True)

    recordings: RecordingInput | list[RecordingInput]
    config_path: str | Path
    output_path: str | Path
    overwrite: bool


BadChannelDetectionConfig = create_model(
    "BadChannelDetectionConfig",
    __config__=ConfigDict(extra="forbid", strict=True),
    **cast(
        dict[str, Any],
        {
            name: (
                parameter.annotation
                if parameter.annotation is not Parameter.empty
                else Any,
                parameter.default if parameter.default is not Parameter.empty else ...,
            )
            for name, parameter in signature(
                detect_bad_channels, eval_str=True
            ).parameters.items()
            if name not in {"recording", "job_kwargs"}
            and parameter.kind
            in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
        },
    ),
)


def _validate_bad_channel_config(config: dict[str, Any]) -> dict[str, Any]:
    """Check SI options without inserting defaults or returning a model."""
    BadChannelDetectionConfig.model_validate(config)
    if config.get("method") == "neighborhood_r2":
        raise ValueError(
            "neighborhood_r2 is not supported as it is developed for LFP stream."
        )
    return config


_raw_metric_constraints: dict[str, dict[str, Any]] = {
    "first_chunk_time_s": {"ge": 0, "allow_inf_nan": False},
    "chunk_size_s": {"gt": 0, "allow_inf_nan": False},
    "num_chunks": {"gt": 0},
    "rolling_rms_window_size_s": {"gt": 0, "allow_inf_nan": False},
}

RawDataQualityMetricsConfig = create_model(
    "RawDataQualityMetricsConfig",
    __config__=ConfigDict(extra="forbid", strict=True),
    **cast(
        dict[str, Any],
        {
            name: (
                parameter.annotation,
                Field(
                    default=parameter.default,
                    **_raw_metric_constraints.get(name, {}),
                ),
            )
            for name, parameter in signature(
                raw_data_quality_metrics, eval_str=True
            ).parameters.items()
            if name
            not in {
                "raw_ap_recording",
                "raw_lfp_recording",
                "preprocessed_ap_recording",
                "folder",
                "verbose",
            }
            and parameter.kind
            in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
        },
    ),
)


def _validate_raw_data_quality_metrics_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate metric options while preserving the supplied dictionary."""
    RawDataQualityMetricsConfig.model_validate(config)
    return config
