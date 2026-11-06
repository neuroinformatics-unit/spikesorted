---
html_theme.sidebar_secondary.remove: true
---

# spikesorted

<div class="spikesorted-home">

`spikesorted` is a configurable extracellular electrophysiology pipeline built on [SpikeInterface](https://spikeinterface.readthedocs.io/).

```{raw} html
:file: includes/front-page/pipeline-animation.html
```

  <nav class="ss-doc-nav" aria-label="Explore the documentation">
    <a class="ss-doc-card" href="getting_started.html"><span class="ss-doc-card-title">Get started</span><span class="ss-doc-card-description">Install <code>spikesorted</code>.</span></a>
    <a class="ss-doc-card" href="tutorials/index.html"><span class="ss-doc-card-title">Tutorials</span><span class="ss-doc-card-description">Guides for common uses of <code>spikesorted</code>.</span></a>
    <a class="ss-doc-card" href="steps/index.html"><span class="ss-doc-card-title">Pipeline Steps</span><span class="ss-doc-card-description">Details on each step in the pipeline.</span></a>
  </nav>

(pipeline-title)=
## Pipeline overview

Apply a modern extracellular electrophysiology pipeline to your recordings, with options to tailor each step to your data.

See the [Roadmap](community/roadmap.md#planned-pipeline-steps) for additional planned steps and features.

<figure class="ss-pipeline">

```{raw} html
:file: includes/front-page/pipeline-diagram.html
```

</figure>

(quality-title)=
## Assess quality

<div class="ss-quality-overview">
<figure class="ss-rms-figure">

```{raw} html
:file: includes/front-page/quality-plot.html
```

<figcaption class="ss-rms-caption">

RMS plots over time are automatically saved, as used for QC in the [IBL pipeline](https://docs.internationalbrainlab.org/_autosummary/ibllib.ephys.ephysqc.html).

</figcaption>
</figure>
<div class="ss-quality-description">

`spikesorted` saves quality metrics and plots to help you quickly assess 
the quality of each recording.

Sorting outputs native SpikeInterface objects that can be 
opened in [spikeinterface-gui](https://spikeinterface-gui.readthedocs.io/en/latest/) for manual curation.

</div>
</div>

(configuration-title)=
## Encode and share

Define your pipeline in a YAML configuration file, improviding reproducability and 
facilatating analysis sharing. 

`spikesorted` comes pre-loaded with popular default cofigurations.
See the [Configs](configs/index.md) page for details, including how to generate your own.

<div class="ss-config-example">
<div class="ss-config-filename">np-standard-kilosort4.yaml</div>

```yaml
raw_data_quality_metrics:
  chunk_size_s: 1.0
  num_chunks: 30
  rolling_rms_window_size_s: 3.0
  quick_metrics_only: false

bad_channel_detection:
  method: 'coherence+psd'

preprocessing:
  remove_bad_channels: {}  # detected bad channels are removed, not interpolated
  phase_shift: {}  # Neuropixels only
  bandpass_filter:
    freq_min: 300.0
    freq_max: 6000.0
  common_reference:
    reference: global
    operator: median

sorting:
  sorter: kilosort4
  params:
    do_CAR: false
    highpass_cutoff: 0.1  # Low cutoff; Kilosort still applies a high-pass filter

postprocessing:
  random_spikes:
    max_spikes_per_unit: 2500
  waveforms:
    ms_before: 1.0
    ms_after: 2.0
  templates: {}
  quality_metrics:
    metric_names: all
  compute_sparsity:
    method: radius
    radius_um: 100
```

</div>

(outputs-title)=
## Standardised outputs

Pipeline outputs are saved in a predefined, standardised folder structure.
This streamlines navigating data and facilitates data sharing,
supporting the development of common analysis tools.

The outputs are fully specified, so you know exactly
what to expect from each pipeline step. See the 
[Specification](specification/index.md) for details on each step and the
[standardised output structure](specification/on-disk-structure.md).

<div class="ss-output-selector">

```{raw} html
:file: includes/front-page/output-symbols.html
```

<figure class="ss-folder-schematic ss-output-multiple">

```{raw} html
:file: includes/front-page/output-multiple.html
```

</figure>
</div>

(python-input)=
(python-title)=
## Flexible data loading

Use [SpikeInterface](https://spikeinterface.readthedocs.io/) to load and prepare
recordings before passing them to `spikesorted`. This is useful for attaching a
custom probe layout or concatenating multiple runs into a session.

This example runs bad-channel detection using your own YAML configuration.

```python
import spikeinterface as si
import probeinterface as pi
from spikesorted import Pipeline

run_1 = si.load("/data/saved_recordings/run_1")
run_2 = si.load("/data/saved_recordings/run_2")

session_1 = si.concatenate_recordings([run_1, run_2])

probe_group = pi.read_prb("my-custom-probe-layout.prb")
session_1.set_probe(probe_group.probes[0])

Pipeline(
    recordings=session_1,
    config_path="my_pipeline.yaml",
    output_path="/results/subject_01",
    stop_after_step="bad_channel_detection",
).run()
```

(try-title)=
## Try `spikesorted`

Running a standard pipeline on an existing recording session is as simple as installing:

```bash
pip install spikesorted
```

and running `spikesorted` through the command line,
pointing it to paths for your session:

```bash
spikesorted \
    --sessions /rawdata/sub-001/ses-001/imec0 \
    --output_path /my_awesome_project/sub-001 \
    --config np-standard-kilosort4
```

You can also run `spikesorted` through the [Python API](tutorials/python-api.md).

We'd love to hear your [feedback](https://github.com/neuroinformatics-unit/spikesorted/issues) and welcome [community contributions](https://github.com/neuroinformatics-unit/spikesorted)!

</div>

```{toctree}
:hidden:
:maxdepth: 2

Get started <getting_started>
Tutorials <tutorials/index>
Config <configs/index>
Pipeline Steps <steps/index>
Spec <specification/index>
Community <community/index>
API <api_index>
```
