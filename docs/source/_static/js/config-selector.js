(() => {
  const form = document.getElementById('config-selector');
  const result = document.getElementById('config-result');
  const preview = document.getElementById('config-yaml');
  let configName;
  const probeSelect = document.getElementById('config-probe');
  const approachSelect = document.getElementById('config-approach');
  const compatibility = document.getElementById('config-compatibility');
  const neuropixelsNote = document.getElementById('config-neuropixels-note');
  const iblNote = document.getElementById('config-ibl-note');
  const updateNotes = () => {
    neuropixelsNote.hidden = probeSelect.value !== 'np1' && probeSelect.value !== 'np2';
    iblNote.hidden = approachSelect.value !== 'ibl-kilosort2_5';
  };
  updateNotes();
  const incompatible = () => probeSelect.value === 'non-neuropixels' && approachSelect.value === 'ibl-kilosort2_5';
  form.addEventListener('change', () => {
    updateNotes();
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
    document.getElementById('config-name').textContent = configName;
    document.getElementById('config-command').textContent = `spikesorted --config ${configName}`;
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
