---
name: comments
description: How to write code comments in spikesorted. Use when adding or editing comments in Python, YAML or Snakemake files.
---

# Writing comments

- Only add a comment when it matters: the code is complicated, or a
  developer would otherwise get something wrong.
- Keep comments short and to the point.
- Only add information the code does not already show, such as why
  something is done, a constraint from SpikeInterface or the spec, or a
  non-obvious consequence.
- Describe the code as it is. Do not refer to older versions or explain
  what was changed and why; that belongs in the commit message.

## Examples

Adds information the code doesn't show:

```python
# IBL detection needs the high frequencies a bandpass filter would remove.
filtered_recording = spre.highpass_filter(recording, freq_min=300)
```

Repeats the code, so leave it out:

```python
# Loop over the recordings
for session_name, shank_id, recording, step_path in self._get_recordings_and_paths():
```

Refers to history, so leave it out or rewrite it to describe the code:

```python
# Changed from .resolve() because it broke mapped drives
output_path = Path(output_path)
```
