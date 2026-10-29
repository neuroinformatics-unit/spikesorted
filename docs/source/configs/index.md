# Configs

```{warning}
These configs are display only. Finalised configuration files coming soon.
Also, it would be nice to have a repository so that people can share their configs.
```

The config (short for 'configurations') files encodes which pipeline steps to run,
and how to run them. By default, spikesorted comes with default configs
that can be used directly or tailored to your recording set up and experimental design.

For full details on the required config structure, see the Config Specification page.
spikesorted fucntions accept either the name of a default config (see below) or
a filepath to a custom configuration file through their `config` argument.

## Select a configuration

You can create a default config file below for inspection (these can be
used directly in spikesorted by passing the config name below to the `config` argument).

For Neuropixels probes, the `phase_shift` is applied during preprocessing. For multi-session
the data can either be concatnated before sorting or unit-matched across sessions. In both cases,
the same bad channels are removed from all recordings passed to spikesorted.

The IBL uses the full IBL pipeline, including saturation detection at the saturation level
of the selected neuropixels probel. Take a look below!

<form id="config-selector">
<div class="ss-config-selector">
  <div class="ss-config-field">
    <label for="config-probe">Select probe</label>
    <select id="config-probe" name="probe" required>
      <option value="" selected disabled>Select a probe</option>
      <option value="np1">Neuropixels 1.0</option>
      <option value="np2">Neuropixels 2.0</option>
      <option value="non-neuropixels">Non-Neuropixels &gt;64 channels</option>
    </select>
  </div>
  <div class="ss-config-field">
    <label for="config-approach">Select approach</label>
    <select id="config-approach" name="approach" required>
      <option value="" selected disabled>Select an approach</option>
      <option value="standard-kilosort4">standard-kilosort4</option>
      <option value="standard-lupin">standard-lupin</option>
      <option value="ibl-kilosort2_5">ibl-kilosort2_5</option>
    </select>
  </div>
  <div class="ss-config-field ss-config-sessions">
    <label for="config-sessions">Session handling</label>
    <select id="config-sessions" name="sessions" required>
      <option value="" selected disabled>Select how to handle sessions</option>
      <option value="separate">Sort sessions separately</option>
      <option value="concat">Concatenate sessions</option>
      <option value="unitmatch">Match sessions with UnitMatch</option>
    </select>
  </div>
</div>

<p id="config-compatibility" role="alert" style="color: #c62828" hidden>IBL is only available for Neuropixels.</p>
<button class="ss-config-button" type="submit">Generate</button>
</form>

<section id="config-result" hidden aria-live="polite">
  <h2>Generated config</h2>
  <p>Save this example as <code id="config-name"></code> and pass its path when you run:</p>
  <pre><code id="config-command"></code></pre>
  <pre><code class="ss-yaml" id="config-yaml"></code></pre>
  <button class="ss-config-button" id="config-save" type="button">Save</button>
</section>

<div id="config-source-np-standard-kilosort4" hidden>

```{literalinclude} np-standard-kilosort4.yaml
:language: yaml
```

</div>

<div id="config-source-np-standard-kilosort4-concat" hidden>

```{literalinclude} np-standard-kilosort4-concat.yaml
:language: yaml
```

</div>

<div id="config-source-np-standard-kilosort4-unitmatch" hidden>

```{literalinclude} np-standard-kilosort4-unitmatch.yaml
:language: yaml
```

</div>

<div id="config-source-standard-kilosort4" hidden>

```{literalinclude} standard-kilosort4.yaml
:language: yaml
```

</div>

<div id="config-source-standard-kilosort4-concat" hidden>

```{literalinclude} standard-kilosort4-concat.yaml
:language: yaml
```

</div>

<div id="config-source-standard-kilosort4-unitmatch" hidden>

```{literalinclude} standard-kilosort4-unitmatch.yaml
:language: yaml
```

</div>

<div id="config-source-np1-ibl-kilosort2_5" hidden>

```{literalinclude} np1-ibl-kilosort2_5.yaml
:language: yaml
```

</div>

<div id="config-source-np1-ibl-kilosort2_5-concat" hidden>

```{literalinclude} np1-ibl-kilosort2_5-concat.yaml
:language: yaml
```

</div>

<div id="config-source-np1-ibl-kilosort2_5-unitmatch" hidden>

```{literalinclude} np1-ibl-kilosort2_5-unitmatch.yaml
:language: yaml
```

</div>

<div id="config-source-np2-ibl-kilosort2_5" hidden>

```{literalinclude} np2-ibl-kilosort2_5.yaml
:language: yaml
```

</div>

<div id="config-source-np2-ibl-kilosort2_5-concat" hidden>

```{literalinclude} np2-ibl-kilosort2_5-concat.yaml
:language: yaml
```

</div>

<div id="config-source-np2-ibl-kilosort2_5-unitmatch" hidden>

```{literalinclude} np2-ibl-kilosort2_5-unitmatch.yaml
:language: yaml
```

</div>

<div id="config-source-np-standard-lupin" hidden>

```{literalinclude} np-standard-lupin.yaml
:language: yaml
```

</div>

<div id="config-source-np-standard-lupin-concat" hidden>

```{literalinclude} np-standard-lupin-concat.yaml
:language: yaml
```

</div>

<div id="config-source-np-standard-lupin-unitmatch" hidden>

```{literalinclude} np-standard-lupin-unitmatch.yaml
:language: yaml
```

</div>

<div id="config-source-standard-lupin" hidden>

```{literalinclude} standard-lupin.yaml
:language: yaml
```

</div>

<div id="config-source-standard-lupin-concat" hidden>

```{literalinclude} standard-lupin-concat.yaml
:language: yaml
```

</div>

<div id="config-source-standard-lupin-unitmatch" hidden>

```{literalinclude} standard-lupin-unitmatch.yaml
:language: yaml
```

</div>

<script>
(() => {
  const form = document.getElementById('config-selector');
  const result = document.getElementById('config-result');
  const preview = document.getElementById('config-yaml');
  let configName;
  const probeSelect = document.getElementById('config-probe');
  const approachSelect = document.getElementById('config-approach');
  const compatibility = document.getElementById('config-compatibility');
  const incompatible = () => probeSelect.value === 'non-neuropixels' && approachSelect.value === 'ibl-kilosort2_5';
  form.addEventListener('change', () => {
    compatibility.hidden = !incompatible();
    result.hidden = true;
  });
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    compatibility.hidden = !incompatible();
    if (incompatible()) {
      result.hidden = true;
      return;
    }
    const selections = new FormData(form);
    const probe = selections.get('probe');
    const approach = selections.get('approach');
    const sessions = selections.get('sessions');
    if (approach === 'ibl-kilosort2_5') {
      configName = `${probe}-${approach}`;
    } else if (probe === 'non-neuropixels') {
      configName = approach;
    } else {
      configName = `np-${approach}`;
    }
    if (sessions !== 'separate') {
      configName += `-${sessions}`;
    }
    document.getElementById('config-name').textContent = `${configName}.yaml`;
    document.getElementById('config-command').textContent = `spikesorted --config ./${configName}.yaml`;
    preview.innerHTML = document.querySelector(`#config-source-${configName} pre`).innerHTML;
    result.hidden = false;
  });
  document.getElementById('config-save').addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([preview.textContent], { type: 'text/yaml' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = `${configName}.yaml`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
})();
</script>

For the supported pipeline settings, see the [configuration specification](../specification/config.md).
