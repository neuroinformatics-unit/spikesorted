# Config

The example configs use `output.structure: neuroblueprint`. Change this to
`by_session` or `by_step` to select a different
[output folder layout](../specification/on-disk-structure.md).

Preprocessing saves samples and SpikeInterface metadata in `preprocessing/recording/`
by default. Set `output.save_preprocessed_recording: false` to retain a lazy
recording and write only SpikeInterface's `metadata.json` and stage plots.
The metadata-only mode requires a JSON-serializable recording and its source files
to remain available. Both modes write `preprocessing_plots/start/`, `middle/`, and `end/`, showing
the first second, a second centred on the exact midpoint, and the final second
before preprocessing and after each configured operation. Recordings shorter
than one second use their full duration in each folder. Existing
preprocessing output requires `overwrite=True` and is replaced in either mode.


```{warning}
These configs are display only. Finalised configuration files coming soon.
```

The **Config** file encodes which pipeline steps are run, and how they are run.

`spikesorted` provides default configs  that can be used directly or tailored to your recording setup and experimental design.

For full details on the required config structure, see the [Config Specification](../specification/config.md) page.

To generate your own configs, create a new [YAML file](../specification/config.md#config-structure) from scratch,
or generate, save and edit a configuration file below. `spikesorted` functions accept
either the name of a default `config` name or path to a custom configuration file.

## Select a configuration

You can generate and download an example config file below for inspection. Alternatively,
these settings can be used in `spikesorted` by using the default keyword arguments as suggested
after generation.

```{include} selector.md
```

<!-- Edit config-notes-neuropixels.md and config-notes-ibl.md to update the descriptions shown for the selected options. -->
