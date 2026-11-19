"""Shared output layout for pipeline writers and loaders."""

from pathlib import Path


def get_step_output_path(output_path, config, step_name, session_name, shank_id=None):
    """Resolve a step directory using the configured output layout."""
    structure = config.get("output", {}).get("structure", "neuroblueprint")
    shank = () if shank_id is None else (f"shank_{shank_id}",)
    layouts = {
        "neuroblueprint": (session_name, "ephys", *shank, step_name),
        "by_session": (session_name, step_name, *shank),
        "by_step": (step_name, session_name, *shank),
    }
    return Path(output_path).joinpath(*layouts[structure])
