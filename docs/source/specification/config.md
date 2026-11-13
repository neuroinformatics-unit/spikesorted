# Config specification

This specification defines the structure and valid contents of the [Config file](../configs/index.md).

An example including every step, with a subset of available arguments for each, is shown below:

```yaml
output:
  structure: neuroblueprint

raw_data_quality_metrics:
  chunk_size_s: 1.0
  num_chunks: 30
  rolling_rms_window_size_s: 3.0
  quick_metrics_only: false

bad_channel_detection:
  method: 'coherence+psd'

artifact_detection:
  detect_saturation_periods:
    saturation_threshold_uV: 1200.0  # NP1 saturation voltage
    diff_threshold_uV: 300.0         # Determined by IBL
    proportion: 0.2

preprocessing:
  highpass_filter:
    freq_min: 300.0
  phase_shift: {}
  interpolate_bad_channels: {}
  highpass_spatial_filter: {}
  silence_periods:
    mode: zeros

combine_sessions:
  method: concatenate

sorting:
  sorter: kilosort2_5
  params:
    car: false
    freq_min: 0.1
    do_correction: true

postprocessing:
  random_spikes:
    max_spikes_per_unit: 2500
  waveforms:
    ms_before: 1.0
    ms_after: 2.0

curation: {}
```

## Config structure

Configs are stored in a [YAML](https://yaml.org/) file, where each pipeline step
is an entry in the file. To skip a step, omit its entry from the YAML file.
Only optional steps can be skipped.

| Step name | Description | Optional |
| --- | --- | --- |
| `raw_data_quality_metrics` | Compute quality metrics for the raw recording. | Yes |
| `bad_channel_detection` | Identify and classify bad channels. | Yes |
| `artifact_detection` | Detect periods containing recording artifacts. | Yes |
| `preprocessing` | Apply filters, channel handling, and artifact removal before sorting. | No |
| `combine_sessions` | Combine preprocessed sessions for sorting. | Yes |
| `sorting` | Run the selected spike sorter. | No |
| `postprocessing` | Compute waveforms, templates, quality metrics, and other sorting analyzer extensions. | No |
| `curation` | Curate sorted units through labeling, merging, and removal. | Yes |

```{note}
It is best practice to include all applicable steps, especially raw data quality
metrics and bad channel detection.
```

## Output layout

The optional `output` section controls folder organisation; it is not a pipeline step.
Set `output.structure` to `neuroblueprint` (the default), `by_session`, or `by_step`.
Omitting `output` or `structure` selects `neuroblueprint`.

Pass the subject directory, for example `results/sub-001`, as `output_path`.
See [Structure on disk](on-disk-structure.md) for folder trees and session-union paths.

## Step parameters

### Bad channel detection

All supported parameters and their descriptions can be found in the
[SpikeInterface documentation](https://spikeinterface.readthedocs.io/en/stable/api.html#spikeinterface.preprocessing.detect_bad_channels) (version `0.105.3`).

The key parameters are listed below.

``method``

This selects the bad channel detection method to use. `coherence+psd`,
the method of the IBL's bad channel detection is recommended.

The key thresholds for this method can be adjusted to change detection sensitivity.
The defaults are designed for Neuropixels 1.0 probes.

| Threshold | Default | Description | Effect of lowering the threshold |
| --- | --- | --- | --- |
| `psd_hf_threshold` | `0.02` µV²/Hz | Flags channels whose mean power spectral density above 80% of the Nyquist frequency exceeds this threshold. | More sensitive to high-frequency noise. |
| `dead_channel_threshold` | `-0.5` | Flags channels whose similarity to the probe-wide median signal, after subtracting the local trend across channels, falls below this threshold. | Less sensitive to dead channels. |
| `noisy_channel_threshold` | `1.0` | Flags channels whose similarity to the probe-wide median signal, after subtracting the local trend across channels, exceeds this threshold. | More sensitive to noisy channels. |
| `outside_channel_threshold` | `-0.75` | Flags contiguous channels at the selected probe ends where the local similarity trend falls below this threshold plus one. | Less sensitive to channels outside the brain. |

Either noise criterion can flag a channel as noisy; both do not need to be met.

| Setting | Default | Description |
| --- | --- | --- |
| `n_neighbors` | `11` | Window size, in channels, for the median filter used to estimate the local similarity trend. It must be odd. A smaller window may help for lower-density probes. |
| `outside_channels_location` | `top` | Specifies whether outside-brain channels can be detected at the `top`, `bottom`, or `both` ends of the probe. |
