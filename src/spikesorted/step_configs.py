"""Canonical operation groups for step ordering rules.

These groups are not a complete list of supported SpikeInterface preprocessors.
"""

TEMPORAL_FILTERS = (
    "filter",
    "bandpass_filter",
    "highpass_filter",
    "notch_filter",
    "gaussian_filter",
)

SPATIAL_OPERATIONS = ("common_reference", "highpass_spatial_filter")


def get_bad_channel_step(preprocessing) -> str | None:
    """Select the bad-channel operation after mutual-exclusion validation."""
    if "remove_bad_channels" in preprocessing:
        return "remove_bad_channels"
    elif "interpolate_bad_channels" in preprocessing:
        return "interpolate_bad_channels"
    else:
        return None
