<form id="config-selector">
<div class="ss-config-selector">
  <div class="ss-config-field">
    <label for="config-probe">Select probe</label>
    <select id="config-probe" name="probe" required>
      <option value="np1">Neuropixels 1.0</option>
      <option value="np2">Neuropixels 2.0</option>
      <option value="non-neuropixels">Non-neuropixels (&gt; 64 channels)</option>
    </select>
  </div>
  <div class="ss-config-field">
    <label for="config-approach">Select approach</label>
    <select id="config-approach" name="approach" required>
      <option value="standard-kilosort4">Standard Kilosort4</option>
      <option value="ibl-kilosort2_5">International Brain Laboratory (IBL)</option>
    </select>
  </div>
  <div class="ss-config-field ss-config-sessions">
    <label for="config-sessions">Session handling</label>
    <select id="config-sessions" name="sessions" required>
      <option value="separate">Single session (or individual sessions sorted separately)</option>
      <option value="concat">Concatenate sessions</option>
    </select>
  </div>
</div>

<p id="config-compatibility" role="alert" style="color: #c62828" hidden>IBL is only available for Neuropixels.</p>

<button class="ss-config-button" type="submit">Generate</button>
</form>

<section id="config-result" hidden aria-live="polite">
  <h2>Generated config</h2>

<div class="ss-config-notes" id="config-neuropixels-note" hidden>

```{include} /configs/config-notes-neuropixels.md
```

</div>

<div class="ss-config-notes" id="config-ibl-note" hidden>

```{include} /configs/config-notes-ibl.md
```

</div>

  <p>Save this example as <code id="config-name"></code> and pass its path when you run:</p>
  <pre><code id="config-command"></code></pre>
  <pre><code class="ss-yaml" id="config-yaml"></code></pre>
  <button class="ss-config-button" id="config-save" type="button">Save</button>
</section>

<div id="config-source-np-standard-kilosort4" hidden>

```{literalinclude} /configs/example-configs/np-standard-kilosort4.yaml
:language: yaml
```

</div>

<div id="config-source-np-standard-kilosort4-concat" hidden>

```{literalinclude} /configs/example-configs/np-standard-kilosort4-concat.yaml
:language: yaml
```

</div>

<div id="config-source-np-standard-kilosort4-unitmatch" hidden>

```{literalinclude} /configs/example-configs/np-standard-kilosort4-unitmatch.yaml
:language: yaml
```

</div>

<div id="config-source-standard-kilosort4" hidden>

```{literalinclude} /configs/example-configs/standard-kilosort4.yaml
:language: yaml
```

</div>

<div id="config-source-standard-kilosort4-concat" hidden>

```{literalinclude} /configs/example-configs/standard-kilosort4-concat.yaml
:language: yaml
```

</div>

<div id="config-source-standard-kilosort4-unitmatch" hidden>

```{literalinclude} /configs/example-configs/standard-kilosort4-unitmatch.yaml
:language: yaml
```

</div>

<div id="config-source-np1-ibl-kilosort2_5" hidden>

```{literalinclude} /configs/example-configs/np1-ibl-kilosort2_5.yaml
:language: yaml
```

</div>

<div id="config-source-np1-ibl-kilosort2_5-concat" hidden>

```{literalinclude} /configs/example-configs/np1-ibl-kilosort2_5-concat.yaml
:language: yaml
```

</div>

<div id="config-source-np1-ibl-kilosort2_5-unitmatch" hidden>

```{literalinclude} /configs/example-configs/np1-ibl-kilosort2_5-unitmatch.yaml
:language: yaml
```

</div>

<div id="config-source-np2-ibl-kilosort2_5" hidden>

```{literalinclude} /configs/example-configs/np2-ibl-kilosort2_5.yaml
:language: yaml
```

</div>

<div id="config-source-np2-ibl-kilosort2_5-concat" hidden>

```{literalinclude} /configs/example-configs/np2-ibl-kilosort2_5-concat.yaml
:language: yaml
```

</div>

<div id="config-source-np2-ibl-kilosort2_5-unitmatch" hidden>

```{literalinclude} /configs/example-configs/np2-ibl-kilosort2_5-unitmatch.yaml
:language: yaml
```

</div>

<div id="config-source-np-standard-lupin" hidden>

```{literalinclude} /configs/example-configs/np-standard-lupin.yaml
:language: yaml
```

</div>

<div id="config-source-np-standard-lupin-concat" hidden>

```{literalinclude} /configs/example-configs/np-standard-lupin-concat.yaml
:language: yaml
```

</div>

<div id="config-source-np-standard-lupin-unitmatch" hidden>

```{literalinclude} /configs/example-configs/np-standard-lupin-unitmatch.yaml
:language: yaml
```

</div>

<div id="config-source-standard-lupin" hidden>

```{literalinclude} /configs/example-configs/standard-lupin.yaml
:language: yaml
```

</div>

<div id="config-source-standard-lupin-concat" hidden>

```{literalinclude} /configs/example-configs/standard-lupin-concat.yaml
:language: yaml
```

</div>

<div id="config-source-standard-lupin-unitmatch" hidden>

```{literalinclude} /configs/example-configs/standard-lupin-unitmatch.yaml
:language: yaml
```

</div>

<script src="../_static/js/config-selector.js"></script>
