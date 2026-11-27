"""Shared output layout for pipeline writers and loaders."""

from pathlib import Path


def get_step_output_path(output_path, step_name, session_name, shank_id):
    """Return a step's output folder for one session and shank.

    Shared by the steps that write outputs and the steps that read them, so
    both use the layout ``<session>/ephys/shank-<id>/<step>``.

    Parameters
    ----------
    output_path
        The subject folder.
    step_name
        Name of the step, which is also its folder name.
    session_name
        Name of the session.
    shank_id
        Shank ID.

    Returns
    -------
    step_path
        The step's output folder.
    """
    return Path(output_path).joinpath(
        session_name, "ephys", f"shank-{shank_id}", step_name
    )
