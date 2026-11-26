"""Command-line interface: run the spikesorted workflow with Snakemake."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

from spikesorted.utils.utils import load_pipeline_config

SNAKEFILE_PATH = Path(__file__).parent / "workflow" / "Snakefile"


def main(argv: list[str] | None = None) -> int:
    """Run the pipeline on one subject's sessions from the command line.

    Writes the sessions and config to a run config, then runs the Snakemake
    workflow on this machine.

    Parameters
    ----------
    argv
        Command-line arguments, or None to read them from ``sys.argv``.

    Returns
    -------
    exit_code
        Snakemake's exit code.

    Examples
    --------
    .. code-block:: console

        spikesorted --sessions ses-001=/data/ses-001/recording \\
            --config config.yaml --output /derivatives/sub-001
    """
    parser = argparse.ArgumentParser(
        prog="spikesorted",
        description="Run the spikesorted pipeline on one subject's sessions.",
    )
    parser.add_argument(
        "--sessions",
        nargs="+",
        required=True,
        metavar="NAME=PATH",
        help=(
            "Recordings to process, as NAME=PATH. PATH is a SpikeGLX or Open "
            "Ephys recording, or a SpikeInterface .json/.pkl dump or saved "
            "folder. NAME can be omitted when exactly one folder "
            "in PATH starts with 'ses-'; that folder name is then used."
        ),
    )
    parser.add_argument(
        "--config", required=True, type=Path, help="Path to the pipeline YAML config."
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="The subject folder to write outputs to, e.g. derivatives/sub-001.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List the jobs that would run, without running them.",
    )
    cli_arguments = parser.parse_args(argv)

    config_path = cli_arguments.config.absolute()
    output_path = cli_arguments.output.absolute()

    # Validate the config before writing anything.
    load_pipeline_config(config_path)

    session_names = []
    recording_paths = {}
    for session_argument in cli_arguments.sessions:
        session_name, recording_path = _parse_session_argument(parser, session_argument)
        session_names.append(session_name)
        recording_paths[session_name] = recording_path.as_posix()

    if len(recording_paths) != len(session_names):
        parser.error(f"Session names must be unique: {session_names}")

    run_config_path = output_path / ".spikesorted" / "run_config.yaml"
    run_config_path.parent.mkdir(parents=True, exist_ok=True)
    with run_config_path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(
            {
                "output_path": output_path.as_posix(),
                "config_path": config_path.as_posix(),
                "sessions": recording_paths,
            },
            file,
            sort_keys=False,
        )

    snakemake_command = [
        sys.executable,
        "-m",
        "snakemake",
        "--snakefile",
        str(SNAKEFILE_PATH),
        "--configfile",
        str(run_config_path),
        "--directory",
        str(output_path),
        "--cores",
        "1",
        # The default file backend names a metadata file after each output's
        # full path, which goes over the Windows path-length limit.
        "--persistence-backend",
        "db",
    ]
    if cli_arguments.dry_run:
        snakemake_command.append("--dry-run")

    return subprocess.run(snakemake_command, check=False).returncode


def _parse_session_argument(
    parser: argparse.ArgumentParser, session_argument: str
) -> tuple[str, Path]:
    """Return the session name and recording path from one ``--sessions`` value.

    Parameters
    ----------
    parser
        The CLI parser, used to report an argument error.
    session_argument
        A ``NAME=PATH`` value, or a path containing exactly one folder whose
        name starts with ``ses-``, which is then used as the session name.

    Returns
    -------
    session_name_and_path
        The session name and the absolute recording path.
    """
    if "=" in session_argument:
        session_name, recording_path = session_argument.split("=", 1)
        return session_name, Path(recording_path).absolute()

    recording_path = Path(session_argument).absolute()

    session_folder_names = []
    for folder_name in recording_path.parts:
        if folder_name.startswith("ses-"):
            session_folder_names.append(folder_name)

    if len(session_folder_names) != 1:
        parser.error(
            f"Cannot find a session name for {session_argument}: its path has "
            f"{len(session_folder_names)} folders starting with 'ses-' "
            f"{session_folder_names}, but needs exactly one. Pass the session "
            "explicitly as NAME=PATH."
        )

    return session_folder_names[0], recording_path


if __name__ == "__main__":
    sys.exit(main())
