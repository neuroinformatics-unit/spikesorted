# Configs

Coming soon...

## Session handling

Concatenated sorting is configured with:

```yaml
combine_sessions:
  method: concatenate
```

This combines the preprocessed recordings before sorting, using SpikeInterface's
`concatenate_recordings`, while retaining session boundaries.

For separately sorted sessions, optional matching after postprocessing is configured with:

```yaml
unitmatching:
  method: unitmatch
  params:
    channel_radius: 150
    max_dist: 100
    neighbour_dist: 50
    match_threshold: 0.5
    units_per_shank_thrs: 15
```

`unitmatch` refers to UnitMatchPy using per-session SpikeInterface SortingAnalyzers,
following its [SpikeInterface integration example](https://github.com/EnnyvanBeest/UnitMatch/blob/main/UnitMatchPy/Demo%20Notebooks/UMPy_spike_interface_demo.ipynb).
`params` supplies overrides to UnitMatchPy's parameter dictionary.
It is not a native SpikeInterface 0.105.3 method. The adapter must prepare the
waveform and channel-position inputs required by UnitMatchPy. Both configuration
sections describe planned pipeline support; neither is implemented yet.

## Quality metric selection

`postprocessing.quality_metrics.metric_names: all` will be supported as a
spikesorted shorthand for every quality metric registered in the installed
SpikeInterface version, including metrics excluded from its default selection
(such as `nn_advanced`). The pipeline must expand `all` into an explicit list of
metric names before passing it to SpikeInterface; SpikeInterface does not accept
the string `all` directly. This translation is not yet implemented.

## Saturation threshold

`artifact_detection.detect_saturation_periods.saturation_threshold_uV` will
accept either a numeric threshold in microvolts or `from_metadata`.
The pipeline must translate `from_metadata` to `None` when calling
SpikeInterface's `detect_saturation_periods`, which reads the recording's
`saturation_threshold_uV` annotation. Neuropixels extractors populate this
annotation from the ADC peak-to-peak voltage range and recording gain when
available: `(adc_range_vpp / 2) / gain * 1e6`.

This uses the metadata-derived limit directly, without a safety factor. If the
annotation is unavailable, SpikeInterface raises an error and a numeric threshold
must be supplied. The `from_metadata` translation is not yet implemented.
