---
name: docstrings
description: How to write docstrings in spikesorted. Use when writing or editing a docstring for a module, class, function or method.
---

# Writing docstrings

Use the [numpydoc](https://numpydoc.readthedocs.io/en/latest/format.html) format.

## Rules for every docstring

- Start with a one-line summary.
- Use `Parameters` and `Returns` sections. Leave out a section when there is
  nothing to put in it (no arguments, or nothing returned).
- Do not put types in the docstring. Types belong in the signature's type
  hints, so write `output_path` rather than `output_path : Path`.

## User-facing code

User-facing code is what users call or construct themselves, such as
`Pipeline`, the step classes and the slurm entry points.

- Write the summary and description for someone new to spikesorted.
  Explain concisely what the function or class is for and when to use it,
  not how it works inside.
- Add an `Examples` section showing a typical call.

```python
def run_pipeline_with_slurm(recordings, config_path, output_path, slurm_opts=None):
    """Run the pipeline on a SLURM cluster, one job per session and shank.

    Use this instead of `Pipeline.run()` when recordings are too large or
    too many to process on one machine. The call returns as soon as the
    coordinator job is submitted.

    Parameters
    ----------
    recordings
        The recordings to process: a recording, a dict of recordings by
        shank, or a list with one entry per session.
    config_path
        Path to the pipeline YAML config.
    output_path
        Absolute path to the folder where outputs are written.
    slurm_opts
        SLURM settings for the worker jobs, such as `slurm_partition`
        and `mem_gb`.

    Returns
    -------
    job
        The submitted coordinator job. Call `job.result()` to wait for
        completion and raise any worker errors.

    Examples
    --------
    >>> job = run_pipeline_with_slurm(
    ...     recordings=[recording_1, recording_2],
    ...     config_path="config.yaml",
    ...     output_path="/ceph/project/derivatives",
    ...     slurm_opts={"conda_env_name": "spikesorted", "slurm_partition": "cpu"},
    ... )
    """
```

## Internal code

Internal code is everything users don't call directly: private (`_`)
functions and methods, and helpers used only inside the package.

- Keep it short: say what the function is for.
- Add where it sits in the codebase only if the purpose isn't clear
  without it.
- No `Examples` section.

```python
def get_step_output_path(output_path, config, step_name, session_name, shank_id=None):
    """Return a step's output folder for one session and shank.

    Shared by the steps that write outputs and the steps that read them,
    so both follow the layout set in the config.

    Parameters
    ----------
    output_path
        The pipeline's output root.
    config
        The loaded pipeline config.
    step_name
        Name of the step, which is also its folder name.
    session_name
        Name of the session.
    shank_id
        Shank ID, or None when recordings are not split by shank.

    Returns
    -------
    step_path
        The step's output folder.
    """
```
