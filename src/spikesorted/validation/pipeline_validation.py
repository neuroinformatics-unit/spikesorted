"""Validation of pipeline execution boundaries."""

PIPELINE_STEP_NAMES = (
    "bad_channel_detection",
    "raw_data_quality_metrics",
    "artifact_detection",
)


def validate_pipeline_steps(
    start_at_step: str | None,
    stop_after_step: str | None,
) -> None:
    """Require known execution boundaries in pipeline order."""
    for argument, step_name in (
        ("start_at_step", start_at_step),
        ("stop_after_step", stop_after_step),
    ):
        if step_name is not None:
            if step_name not in PIPELINE_STEP_NAMES:
                raise ValueError(
                    f"Unknown {argument}={step_name!r}. "
                    f"Choose from {PIPELINE_STEP_NAMES}."
                )

    if start_at_step is not None and stop_after_step is not None:
        if PIPELINE_STEP_NAMES.index(start_at_step) > PIPELINE_STEP_NAMES.index(
            stop_after_step
        ):
            raise ValueError("start_at_step must not come after stop_after_step.")
