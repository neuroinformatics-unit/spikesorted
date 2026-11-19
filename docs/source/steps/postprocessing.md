---
orphan: true
---

# Postprocessing

The preset configs and
`examples/full_pipeline_test_config.yaml` now explicitly request random spikes,
waveforms, templates, PCA, noise levels, spike amplitudes, spike and unit
locations, template similarity, correlograms, ISI histograms, template metrics,
and all quality metrics. Empty dictionaries use SpikeInterface defaults.

The postprocessing step:

- Pairs each saved sorting with the supplied preprocessed recording. Supply the
  same recording used for sorting, retaining its session and shank names.
- Applies `compute_sparsity` settings when creating the disk-backed analyzer.
- Computes the configured extensions in dependency order, then quality metrics.
  Expands `metric_names: all` to the full list of supported quality metrics.
- Saves `sorting_analyzer/`, `quality_metrics.csv`, and extension parameters in
  each session/shank's postprocessing directory.

The runnable pipeline example includes postprocessing. To run only this step,
set `start_at_step="postprocessing"` and supply the preprocessed recordings and
the output path containing the saved sortings. Existing postprocessing outputs
require `overwrite=True` to replace them. Metrics can be undefined (NaN) for
very short recordings or units with too few spikes.

TODO: expand this page with the individual extension settings. Define the
postprocessing plots required by the specification and document their outputs.
