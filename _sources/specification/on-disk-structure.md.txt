# Structure on disk

```{warning}
This page was written by an LLM and has not yet been reviewed by a human.
```

`output_path` is the root for one subject's results, for example `results/sub-001`.
The pipeline does not add a subject folder or an extra `output` folder to this path.
Select the layout in the pipeline YAML:

```yaml
output:
  structure: neuroblueprint
```

**`neuroblueprint` is the default**, including when the `output` section or its
`structure` field is omitted. The other options are `by_session` and `by_step`.

| Structure | Path below `output_path` |
| --- | --- |
| `neuroblueprint` | `<session>/ephys/<shank>/<step>/` |
| `by_session` | `<session>/<step>/<shank>/` |
| `by_step` | `<step>/<session>/<shank>/` |

Unnamed inputs use `ses-001`, `ses-002`, and so on in input order, including a
single recording. A `(recording, session_name)` or `(path, session_name)` tuple
preserves the supplied session name. Saved recording paths are loaded with
SpikeInterface; their folder names are not used to infer session names.

A shank dictionary creates `shank_<id>` folders, even if it contains only one
shank. A recording supplied without a shank dictionary has no shank folder.
Step folders are not numbered.

## Layout examples

These trees show the implemented bad-channel and artifact detection steps.
The same path convention applies to each step.

::::{tab-set}

:::{tab-item} NeuroBlueprint (default)

```text
sub-001/
├── ses-001/
│   └── ephys/
│       ├── shank_0/
│       │   ├── bad_channel_detection/
│       │   │   ├── bad_channel_ids.csv
│       │   │   └── bad_channel_labels.csv
│       │   └── artifact_detection/
│       │       ├── event_periods.csv
│       │       └── artifact_detection_plots/
│       │           └── artifact_periods.png
│       └── shank_1/
│           ├── bad_channel_detection/
│           └── artifact_detection/
└── ses-002/
    └── ephys/
        ├── shank_0/
        │   ├── bad_channel_detection/
        │   └── artifact_detection/
        └── shank_1/
            ├── bad_channel_detection/
            └── artifact_detection/
```

For a single recording without a shank dictionary:
`sub-001/ses-001/ephys/bad_channel_detection/`.

:::

:::{tab-item} By session

```text
sub-001/
├── ses-001/
│   ├── bad_channel_detection/
│   │   ├── shank_0/
│   │   └── shank_1/
│   └── artifact_detection/
│       ├── shank_0/
│       └── shank_1/
└── ses-002/
    ├── bad_channel_detection/
    │   ├── shank_0/
    │   └── shank_1/
    └── artifact_detection/
        ├── shank_0/
        └── shank_1/
```

For a single recording without a shank dictionary:
`sub-001/ses-001/bad_channel_detection/`.

:::

:::{tab-item} By step

```text
sub-001/
├── bad_channel_detection/
│   ├── ses-001/
│   │   ├── shank_0/
│   │   └── shank_1/
│   └── ses-002/
│       ├── shank_0/
│       └── shank_1/
└── artifact_detection/
    ├── ses-001/
    │   ├── shank_0/
    │   └── shank_1/
    └── ses-002/
        ├── shank_0/
        └── shank_1/
```

For a single recording without a shank dictionary:
`sub-001/bad_channel_detection/ses-001/`.

:::

::::

## Files within a step

The layout changes folder order, not filenames or file contents.
Bad-channel detection writes `bad_channel_ids.csv` and `bad_channel_labels.csv`.
Artifact detection writes `event_periods.csv`; when artifacts are found, it also
writes `artifact_detection_plots/artifact_periods.png`.

See [Inputs and outputs](definitions.md) for the pipeline's data definitions,
including planned outputs for later steps.

## Session unions

When bad channels are combined across sessions, union outputs use
`session_unions` in place of a session name. Each shank's union folder contains
`bad_channel_ids.csv` and `sessions.yaml` recording its contributing sessions.

| Structure | Union path below `output_path` |
| --- | --- |
| `neuroblueprint` | `session_unions/ephys/<shank>/bad_channel_detection/` |
| `by_session` | `session_unions/bad_channel_detection/<shank>/` |
| `by_step` | `bad_channel_detection/session_unions/<shank>/` |

As with individual recordings, the shank folder is omitted when no shank ID is
supplied. Local runs and SLURM coordinators use the same layout.

## SLURM logs and existing results

SLURM logs stay at `<output_path>/slurm_logs/<job_id>/` for every layout.
With `overwrite=False`, each detection step refuses to overwrite an existing
session/shank output folder at its configured location.

Changing `output.structure` affects future reads and writes; it does not move
existing results. Use the same layout throughout a pipeline run so later steps
can find earlier outputs.
