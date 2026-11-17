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
