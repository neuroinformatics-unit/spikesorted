# Pipeline overview

**spikesorted** is a configurable extracellular electrophysiology pipeline built on SpikeInterface. It handles single-session and multi-session workflows, with settings defined in a YAML configuration file.

## From recordings to curated units

The planned workflow covers data loading, bad-channel detection, raw data quality metrics, artifact detection, preprocessing, spike sorting, postprocessing and curation. Sessions can be sorted separately, concatenated for sorting, or matched across sessions with UnitMatch.

Use [Configs](../configs/index.md) to explore configurations, or [Pipeline Steps](../steps/index.md) for the rationale behind each stage.

## Extensive quality-control outputs

The pipeline is designed to produce quality metrics and plots alongside processing results, helping you assess recording quality and inspect the units produced by spike sorting.

- **Recording quality:** bad-channel labels, raw-data quality metrics and plots, and artifact information.
- **Sorting quality:** postprocessing outputs and unit-quality information to support curation.
- **Standardised organisation:** results grouped by pipeline step, session and shank, so outputs can be traced back to their recordings.

Bad-channel detection currently saves channel IDs and labels. Other outputs described here are part of the pipeline design and are still being implemented. See the [output specification](../specification/index.md) and [on-disk structure](../specification/index.md) for details.
