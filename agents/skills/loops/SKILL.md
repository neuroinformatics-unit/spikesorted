---
name: loops
description: When to write a for loop and when a list, dict or set comprehension in spikesorted. Use when building a list, dict or set from another collection, in Python or Snakemake files.
---

# Loops and comprehensions

Use a comprehension only when it fits on one line. Otherwise write a `for`
loop that builds the result.

- One line, one `for`, at most a simple `if`: a comprehension is fine.
- More than one line, more than one `for`, or a long condition: use a loop.
- Use a comprehension over several lines only if the loop would be clearly
  harder to follow, which is rare.

This applies to list, dict and set comprehensions and to generator
expressions passed to functions such as `any()` or `sorted()`.

In Snakemake files, don't hide a multi-line comprehension in a `lambda` for a
rule's `input:`. Write a named input function with a loop instead.

## Examples

Fine, one line:

```python
channel_ids = [str(channel_id) for channel_id in recording.get_channel_ids()]
```

Hard to read, two `for`s over several lines:

```python
manifest = [
    {"session": session_name, "shank": shank_id}
    for session_name in session_names
    for shank_id in InputDataStep.get_shank_ids(recording_paths[session_name])
]
```

Write it as a loop:

```python
manifest = []
for session_name in session_names:
    recording_path = recording_paths[session_name]
    for shank_id in InputDataStep.get_shank_ids(recording_path):
        manifest.append({"session": session_name, "shank": shank_id})
```
