# Config

The example configs use `output.structure: neuroblueprint`. Change this to
`by_session` or `by_step` to select a different
[output folder layout](../specification/on-disk-structure.md).


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
