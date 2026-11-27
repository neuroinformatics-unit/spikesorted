---
name: naming
description: How to name variables, functions, classes and modules in spikesorted. Use when adding or renaming anything in the code.
---

# Naming

## Names should explain themselves

Choose names a reader understands without looking up where the value comes
from. Prefer a longer, specific name to a short, generic one.

| Avoid | Use |
|---|---|
| `path` (for the config file) | `config_path` |
| `rec` | `recording` |
| `out` | `output_path` |
| `ids` | `bad_channel_ids` |
| `kwargs` (for one step's settings) | `detection_kwargs` |

Keep names as short as possible while preserving their meaning. Use `idx`
for an index rather than `i`, even in a short loop.

## Steps, not operations

Call pipeline and preprocessing steps "steps", never "operations". This
applies to variable, function and class names, comments and docstrings, for
example `step_path`, `_check_step_order` and "Apply the configured
preprocessing steps".

## Step module names

Name step modules after what they do, ending in `_step.py`, such as
`bad_channel_detection_step.py`. Never name a module `step.py` or
`steps.py`; the `custom-hooks` pre-commit hook rejects them.
