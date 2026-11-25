# Structure on disk

```{warning}
This page was written by an LLM and has not yet been reviewed by a human.
```

**`output_path` must point to the subject folder**, for example
`derivatives/sub-001`. The pipeline does not add a subject folder or an extra
`output` folder to this path.

Outputs use a fixed, NeuroBlueprint-style layout below `output_path`:

```text
<session>/ephys/shank-<id>/<step>/
```

Unnamed inputs use `ses-001`, `ses-002`, and so on in input order, including a
single recording. A `(recording, session_name)` or `(path, session_name)` tuple
preserves the supplied session name. Saved recording paths are loaded with
SpikeInterface; their folder names are not used to infer session names.

Every recording has a shank folder. The shank ID is the channels' `group`
property, so a single-shank recording uses its one group, for example
`shank-0`. A recording without groups is treated as one shank, `shank-0`.
Step folders are not numbered.

## Layout example

This tree shows the implemented bad-channel and artifact detection steps.
The same path convention applies to each step.

```text
sub-001/
├── ses-001/
│   └── ephys/
│       ├── shank-0/
│       │   ├── bad_channel_detection/
│       │   │   ├── bad_channel_ids.csv
│       │   │   └── bad_channel_labels.csv
│       │   └── artifact_detection/
│       │       ├── event_periods.csv
│       │       └── artifact_detection_plots/
│       │           └── artifact_periods.png
│       └── shank-1/
│           ├── bad_channel_detection/
│           └── artifact_detection/
└── ses-002/
    └── ephys/
        ├── shank-0/
        │   ├── bad_channel_detection/
        │   └── artifact_detection/
        └── shank-1/
            ├── bad_channel_detection/
            └── artifact_detection/
```

## Files within a step

Bad-channel detection writes `bad_channel_ids.csv` and `bad_channel_labels.csv`.
Artifact detection writes `event_periods.csv`; when artifacts are found, it also
writes `artifact_detection_plots/artifact_periods.png`.

See [Inputs and outputs](definitions.md) for the pipeline's data definitions,
including planned outputs for later steps.

## Bad-channel unions

When bad channels are combined across sessions, union outputs use
`bad_channel_unions` in place of a session name. Each shank's union folder contains
`bad_channel_ids.csv` and `sessions.yaml` recording its contributing sessions,
at `bad_channel_unions/ephys/shank-<id>/bad_channel_detection/` below `output_path`.

Local runs and SLURM coordinators use the same layout.

## SLURM logs and existing results

SLURM logs are saved to `<output_path>/slurm_logs/<job_id>/`.
With `overwrite=False`, each detection step refuses to overwrite an existing
session/shank output folder.
