# Structure on disk

This page will contain details on the output folder structure.

Currently the provisional output folder structure is:

::::{tab-set}

:::{tab-item} Single session, single shank

```text
output/
├── raw_data_metrics/
│   ├── raw_data_quality_metrics.csv
│   └── raw_data_quality_plots/
│       └── ...
├── bad_channel_detection/
│   ├── bad_channel_ids.csv
│   └── bad_channel_labels.csv
├── artifact_detection/
│   └── event_periods.csv              # or event_periods_curated.csv
├── preprocessing/
│   ├── metadata.*
│   ├── preprocessing_plots/
│   └── recording/                     # optional, depending on PIPELINE_CONFIG
├── sorting/
│   ├── sorting/
│   └── metadata.*
├── postprocessing/
│   ├── sorting_analyzer/
│   ├── quality_metrics.csv
│   ├── postprocessing_plots/
│   │   └── *.png
│   └── metadata.*
└── curation/
    ├── sorting_analyzer/
    ├── curation_decisions.*
    └── metadata.*
```

:::

:::{tab-item} Multiple sessions, single shank

```text
# Sorting and downstream folders shown for separately sorted sessions.
output/
├── raw_data_metrics/
│   ├── session_0/
│   │   ├── raw_data_quality_metrics.csv
│   │   └── raw_data_quality_plots/
│   │       └── ...
│   └── session_1/
│       ├── raw_data_quality_metrics.csv
│       └── raw_data_quality_plots/
│           └── ...
├── bad_channel_detection/
│   ├── session_0/
│   │   ├── bad_channel_ids.csv
│   │   └── bad_channel_labels.csv
│   ├── session_1/
│   │   ├── bad_channel_ids.csv
│   │   └── bad_channel_labels.csv
│   └── session_unions/               # only when combine_sessions is configured
│       ├── bad_channel_ids.csv
│       └── sessions.yaml
├── artifact_detection/
│   ├── session_0/
│   │   └── event_periods.csv              # or event_periods_curated.csv
│   └── session_1/
│       └── event_periods.csv              # or event_periods_curated.csv
├── preprocessing/
│   ├── session_0/
│   │   ├── metadata.*
│   │   ├── preprocessing_plots/
│   │   └── recording/                     # optional, depending on PIPELINE_CONFIG
│   └── session_1/
│       ├── metadata.*
│       ├── preprocessing_plots/
│       └── recording/                     # optional, depending on PIPELINE_CONFIG
├── sorting/
│   ├── session_0/
│   │   ├── sorting/
│   │   └── metadata.*
│   └── session_1/
│       ├── sorting/
│       └── metadata.*
├── postprocessing/
│   ├── session_0/
│   │   ├── sorting_analyzer/
│   │   ├── quality_metrics.csv
│   │   ├── postprocessing_plots/
│   │   │   └── *.png
│   │   └── metadata.*
│   └── session_1/
│       ├── sorting_analyzer/
│       ├── quality_metrics.csv
│       ├── postprocessing_plots/
│       │   └── *.png
│       └── metadata.*
└── curation/
    ├── session_0/
    │   ├── sorting_analyzer/
    │   ├── curation_decisions.*
    │   └── metadata.*
    └── session_1/
        ├── sorting_analyzer/
        ├── curation_decisions.*
        └── metadata.*
```

:::

:::{tab-item} Multiple sessions, multiple shanks

```text
# Sorting and downstream folders shown for separately sorted sessions.
output/
├── raw_data_metrics/
│   ├── session_0/
│   │   ├── shank_0/
│   │   │   ├── raw_data_quality_metrics.csv
│   │   │   └── raw_data_quality_plots/
│   │   │       └── ...
│   │   └── shank_1/
│   │       ├── raw_data_quality_metrics.csv
│   │       └── raw_data_quality_plots/
│   │           └── ...
│   └── session_1/
│       ├── shank_0/
│       │   ├── raw_data_quality_metrics.csv
│       │   └── raw_data_quality_plots/
│       │       └── ...
│       └── shank_1/
│           ├── raw_data_quality_metrics.csv
│           └── raw_data_quality_plots/
│               └── ...
├── bad_channel_detection/
│   ├── session_0/
│   │   ├── shank_0/
│   │   │   ├── bad_channel_ids.csv
│   │   │   └── bad_channel_labels.csv
│   │   └── shank_1/
│   │       ├── bad_channel_ids.csv
│   │       └── bad_channel_labels.csv
│   ├── session_1/
│   │   ├── shank_0/
│   │   │   ├── bad_channel_ids.csv
│   │   │   └── bad_channel_labels.csv
│   │   └── shank_1/
│   │       ├── bad_channel_ids.csv
│   │       └── bad_channel_labels.csv
│   └── session_unions/               # only when combine_sessions is configured
│       ├── shank_0/
│       │   ├── bad_channel_ids.csv
│       │   └── sessions.yaml
│       └── shank_1/
│           ├── bad_channel_ids.csv
│           └── sessions.yaml
├── artifact_detection/
│   ├── session_0/
│   │   ├── shank_0/
│   │   │   └── event_periods.csv              # or event_periods_curated.csv
│   │   └── shank_1/
│   │       └── event_periods.csv              # or event_periods_curated.csv
│   └── session_1/
│       ├── shank_0/
│       │   └── event_periods.csv              # or event_periods_curated.csv
│       └── shank_1/
│           └── event_periods.csv              # or event_periods_curated.csv
├── preprocessing/
│   ├── session_0/
│   │   ├── shank_0/
│   │   │   ├── metadata.*
│   │   │   ├── preprocessing_plots/
│   │   │   └── recording/                     # optional, depending on PIPELINE_CONFIG
│   │   └── shank_1/
│   │       ├── metadata.*
│   │       ├── preprocessing_plots/
│   │       └── recording/                     # optional, depending on PIPELINE_CONFIG
│   └── session_1/
│       ├── shank_0/
│       │   ├── metadata.*
│       │   ├── preprocessing_plots/
│       │   └── recording/                     # optional, depending on PIPELINE_CONFIG
│       └── shank_1/
│           ├── metadata.*
│           ├── preprocessing_plots/
│           └── recording/                     # optional, depending on PIPELINE_CONFIG
├── sorting/
│   ├── session_0/
│   │   ├── shank_0/
│   │   │   ├── sorting/
│   │   │   └── metadata.*
│   │   └── shank_1/
│   │       ├── sorting/
│   │       └── metadata.*
│   └── session_1/
│       ├── shank_0/
│       │   ├── sorting/
│       │   └── metadata.*
│       └── shank_1/
│           ├── sorting/
│           └── metadata.*
├── postprocessing/
│   ├── session_0/
│   │   ├── shank_0/
│   │   │   ├── sorting_analyzer/
│   │   │   ├── quality_metrics.csv
│   │   │   ├── postprocessing_plots/
│   │   │   │   └── *.png
│   │   │   └── metadata.*
│   │   └── shank_1/
│   │       ├── sorting_analyzer/
│   │       ├── quality_metrics.csv
│   │       ├── postprocessing_plots/
│   │       │   └── *.png
│   │       └── metadata.*
│   └── session_1/
│       ├── shank_0/
│       │   ├── sorting_analyzer/
│       │   ├── quality_metrics.csv
│       │   ├── postprocessing_plots/
│       │   │   └── *.png
│       │   └── metadata.*
│       └── shank_1/
│           ├── sorting_analyzer/
│           ├── quality_metrics.csv
│           ├── postprocessing_plots/
│           │   └── *.png
│           └── metadata.*
└── curation/
    ├── session_0/
    │   ├── shank_0/
    │   │   ├── sorting_analyzer/
    │   │   ├── curation_decisions.*
    │   │   └── metadata.*
    │   └── shank_1/
    │       ├── sorting_analyzer/
    │       ├── curation_decisions.*
    │       └── metadata.*
    └── session_1/
        ├── shank_0/
        │   ├── sorting_analyzer/
        │   ├── curation_decisions.*
        │   └── metadata.*
        └── shank_1/
            ├── sorting_analyzer/
            ├── curation_decisions.*
            └── metadata.*
```

:::

::::
