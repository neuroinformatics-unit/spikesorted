# Definitions

(definitions-raw-data-path)=
## `RAW_DATA_PATH`
A filepath to any raw data files or folders that can be loaded by SpikeInterface (e.g. SpikeGLX, Open Ephys, SpikeInterface folder).

(definitions-spikeinterface-rec)=
## `SPIKEINTERFACE_REC`
An in-memory SpikeInterface [`Recording`](https://spikeinterface.readthedocs.io/en/stable/api.html#spikeinterface.core.BaseRecording) object.

If split by shank, the `SPIKEINTERFACE_REC` may be a dictionary where the keys are shank name and values are recording for that shank e.g. `recording=[{"0": Recording1, "1": Recording2}, {"0": Recording3, "1": Recording4}]`

(definitions-raw-data-path-session-list)=
## `RAW_DATA_PATH_SESSION_LIST`
A Python list of `RAW_DATA_PATH`.

(definitions-spikeinterface-rec-session-list)=
## `SPIKEINTERFACE_REC_SESSION_LIST`
A Python list of `SPIKEINTERFACE_REC`.

(definitions-debugging-rec)=
## `DEBUGGING_REC`
A `SPIKEINTERFACE_REC` that has been cut down to allow the pipeline to run quickly.

The default time to cut a recording down to is 30 seconds, based on the Allen pipeline (as of 02/09/2026).

(definitions-data-loader-output-recordings)=
## `DATA_LOADER_OUTPUT_RECORDINGS`
The data returned by the data loader. It may be a {ref}`SPIKEINTERFACE_REC <definitions-spikeinterface-rec>`, a {ref}`SPIKEINTERFACE_REC_SESSION_LIST <definitions-spikeinterface-rec-session-list>`, a {ref}`DEBUGGING_REC <definitions-debugging-rec>` or list thereof.

(definitions-preprocessed-output-recordings)=
## `PREPROCESSED_OUTPUT_RECORDINGS`
Takes the form `DATA_LOADER_OUTPUT_RECORDINGS` but the recordings are the final output of the preprocessing step.

(definitions-sorting)=
## `SORTING`
A SpikeInterface [`BaseSorting`](https://spikeinterface.readthedocs.io/en/stable/api.html#spikeinterface.core.BaseSorting) object.

(definitions-sorting-analyzer)=
## `SORTING_ANALYZER`
A SpikeInterface [`SortingAnalyzer`](https://spikeinterface.readthedocs.io/en/stable/api.html#spikeinterface.core.SortingAnalyzer) object.

(definitions-sorter-report)=
## `SORTER_REPORT`
The report produced for the SpikeInterface sorting result.

(definitions-postprocessing-plots)=
## `POSTPROCESSING_PLOTS`
The collection of plots generated during postprocessing.

**TODO: fill in** (for the most part these will )

(definitions-template-plots)=
### `TEMPLATE_PLOTS`
(definitions-waveform-plots)=
### `WAVEFORM_PLOTS`
(definitions-cluster-plots)=
### `CLUSTER_PLOTS`
(definitions-unit-location-plots)=
### `UNIT_LOCATION_PLOTS`
(definitions-autocorrelogram-plots)=
### `AUTOCORRELOGRAM_PLOTS`
(definitions-crosscorrelogram-plots)=
### `CROSSCORRELOGRAM_PLOTS`
(definitions-firing-rate-plots)=
### `FIRING_RATE_PLOTS`
(definitions-quality-metric-plots)=
### `QUALITY_METRIC_PLOTS`

## Inputs


(outputs-concat-rec-times)=
### `CONCAT_REC_TIMES`
A CSV or [pandas `DataFrame`](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html) containing the start and stop times of sessions which have been concatenated. This can be used by the pipeline to split the sorting.

Each row contains the start and stop times of one session, in seconds.

The two columns are:

- `"start_time"`: session start time, as a float
- `"stop_time"`: session stop time, as a float

(outputs-probe)=
### `PROBE`
A ProbeInterface [`Probe`](https://probeinterface.readthedocs.io/en/main/api.html#probeinterface.Probe) object.

(outputs-output-path)=
### `OUTPUT_PATH`
The root directory for the pipeline output. Here outputs from steps are saved and used as inputs for following steps.

(outputs-pipeline-config)=
### `PIPELINE_CONFIG`
The YAML configuration file for the pipeline. See [Configs](config.md).

## Outputs

(outputs-raw-data-quality-metrics)=
### `RAW_DATA_QUALITY_METRICS`
A set of metrics that estimate the quality of raw data, based on the IBL [spike-sorting white paper](https://doi.org/10.6084/m9.figshare.19705522). 

For steps that are measured after preprocessing, `phase_shift`, a TEMPORAL_FILTER and COMMON_REFERENCE step are applied, based on the PIPELINE_CONFIG.

These metrics are computed and stored on disk, and used to generate {ref}`RAW_DATA_QUALITY_PLOTS <outputs-raw-data-quality-plots>`. No hard thresholds are applied to these metrics to determine inclusion or exclusion of data, instead this is decided by visual inspection of the plots.

**Before and after preprocessing:**

- **RMS (AP and LFP bands):** To obtain a quick measure of data quality, RMS is computed from one 1-second chunk every 300 seconds. The following summary metrics are then calculated:

    - Median RMS per channel across the sampled chunks.
    - 10th and 90th percentiles of the per-channel median RMS values, providing a measure of RMS variability across the probe.

    A full per-channel RMS map is then computed across the entire recording using consecutive windows approximately 3 seconds long (8192 samples for a Neuropixels 1.0 probe). These maps are used to generate {ref}`RAW_DATA_QUALITY_PLOTS <outputs-raw-data-quality-plots>`.

**After preprocessing:**

- **Spectral Density AP** AP-band power spectral density in $V^2/Hz$ computed per channel using Welch's method.
- **Spectral Density LFP** LFP-band power spectral density in $V^2/Hz$ computed per channel using Welch's method.
- **Spike Rate** spike-like events per second from simple threshold detection on the preprocessed AP signal. These spikes can be overlaid on the RMS or raw data to get a first idea if any spikes are detectable from the data and if issues in the RMS appear to translate to issues in spike detection.

**TODO: specify format for storage**
**TODO: determine chunking rules**

(outputs-raw-data-quality-plots)=
### `RAW_DATA_QUALITY_PLOTS`
Plots used for quality-assessment, saved as `.png`. These are computed from the `RAW_DATA_QUALITY_METRICS` as developed by the [IBL](https://doi.org/10.6084/m9.figshare.19705522).

- **AP-band and LFP-band RMS**: a time x channel plot of RMS. Separate plots contrasting before and after preprocessing.
- **Spikes on RMS**: time x channel preprocessed RMS plot with detected spike time overlaid.
- **AP-band and LFP-band Spectral Density**: a channel x frequency heatmap with intensity representing power, $V^2/Hz$

(outputs-bad-channel-detection-outputs)=
### `BAD_CHANNEL_DETECTION_OUTPUTS`
Outputs from the {ref}`detect bad channels step <pipeline-steps-detect-bad-channels>`.

(outputs-bad-channel-ids)=
#### `BAD_CHANNEL_IDS`
The channel IDs identified as bad by the detect-bad-channels step.

**TODO:** Document cross-session bad-channel ID unions for concatenation and unit matching, including per-shank behavior, the `session_unions` directory, and `sessions.yaml` alongside each union CSV listing the contributing session names and generation date.

(outputs-bad-channel-labels)=
#### `BAD_CHANNEL_LABELS`
The bad-channel classification associated with each `BAD_CHANNEL_ID`.

(outputs-artefact-detection-plots)=
### `ARTEFACT_DETECTION_PLOTS`
A plot of a random selection of detected artefact periods denoted by a linear region overlaid on the preprocessed data.

(outputs-preprocess-step-plots)=
### `PREPROCESS_STEP_PLOTS`
A plot of the data at each preprocessing stage.

(outputs-motion-correction-plots)=
### `MOTION_CORRECTION_PLOTS`
See [plot_motion()](https://spikeinterface.readthedocs.io/en/latest/api.html#spikeinterface.widgets.plot_motion).

(outputs-session-concatenation-plots)=
### `SESSION_CONCATENATION_PLOTS`
Plots that show the preprocessed data across the concatenation points for each session. 
**TODO:** this could be supplemented by quality metrics across these boundaries, inter-session alignment plots.


(outputs-artefact-periods-csv)=
### `ARTEFACT_PERIODS_CSV`
A CSV or [pandas `DataFrame`](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html) containing the start and stop times of periods
detected as artefacts.

Each row is a detected period.

The three columns are:

- `"start_time"`: taking float values
- `"stop_time"`: taking float values
- (optional) `label`: Label of the event period. Permitted values are `SATURATION` or `ENVELOPE`. 

(outputs-artefact-periods-curated-csv)=
### `ARTEFACT_PERIODS_CURATED_CSV`
An `ARTEFACT_PERIODS_CURATED_CSV` is a CSV file that has been curated. It is the same format of
`ARTEFACT_PERIODS_CSV`. It indicates it has been manually curated by including the suffix `_curated`
in the filename.

(outputs-quality-metrics-csv)=
### `QUALITY_METRICS_CSV`
Per-unit quality metrics table, following SpikeInterface quality metrics in [`quality_metrics.metric_names`](https://github.com/AllenNeuralDynamics/aind-ephys-pipeline/blob/main/docs/source/parameters.rst):

**TODO:** log and/or link to the exact quality metrics used and their definitions

