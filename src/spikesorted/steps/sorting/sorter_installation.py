"""Install MATLAB Kilosort revisions for use with SpikeInterface."""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Literal

from spikeinterface.sorters import Kilosort2_5Sorter, Kilosort3Sorter


def get_sorter_installation_path(
    sorter_name: Literal["kilosort2_5", "kilosort3"],
) -> Path:
    """Return the shared location used to install and discover the sorter."""
    return Path.home() / ".spikesorted" / "sorters" / sorter_name


def install_kilosort(
    sorter_name: Literal["kilosort2_5", "kilosort3"],
) -> Path:
    """Download a pinned commit, build its MEX files, and register its path.

    MATLAB and Git must be on PATH. MATLAB needs a configured CUDA/C++ compiler
    and the toolboxes required by Kilosort. Incomplete installations are retried
    in the same folder. Registration applies to this process and its subprocesses.
    """
    # Latest MouseLand/Kilosort branch commits retrieved on 2026-11-19.
    commits = {
        "kilosort2_5": "f2e570c61b6e920d361bcae6e2350bea03a16506",  # kilosort25
        "kilosort3": "c43f52452e474024a75ffed4152bce1ebede4eed",  # kilosort3
    }
    commit = commits[sorter_name]

    matlab = shutil.which("matlab")
    if matlab is None:
        raise FileNotFoundError("MATLAB is not installed or is not available on PATH.")

    matlab_command = [matlab]
    if sys.platform == "win32":
        matlab_command.append("-wait")
    # Confirm MATLAB can start before downloading the sorter.
    subprocess.run([*matlab_command, "-batch", "disp(version)"], check=True)

    sorter_path = get_sorter_installation_path(sorter_name)
    sorter_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", str(sorter_path)], check=True)
    subprocess.run(
        [
            "git", "-C", str(sorter_path), "fetch", "--depth", "1", "--",
            "https://github.com/MouseLand/Kilosort.git", commit,
        ],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(sorter_path), "checkout", "--detach", "FETCH_HEAD"],
        check=True,
    )

    subprocess.run(
        [*matlab_command, "-batch", "mexGPUall"],
        cwd=sorter_path / "CUDA",
        check=True,
    )
    if not _has_kilosort_mex_files(sorter_name, sorter_path):
        raise FileNotFoundError(f"Kilosort MEX build is incomplete at {sorter_path}.")
    _set_kilosort_path(sorter_name, sorter_path)
    return sorter_path


def ensure_kilosort_installed(
    sorter_name: Literal["kilosort2_5", "kilosort3"],
) -> bool:
    """Reuse a built installation or install it, then register it with SI."""
    sorter_path = get_sorter_installation_path(sorter_name)
    if sorter_path.is_dir() and _has_kilosort_mex_files(sorter_name, sorter_path):
        _set_kilosort_path(sorter_name, sorter_path)
    else:
        install_kilosort(sorter_name)
    return True


def _has_kilosort_mex_files(sorter_name, sorter_path) -> bool:
    """Check all MEX outputs of the pinned version's CUDA/mexGPUall.m script."""
    mex_extension = {"win32": "mexw64", "linux": "mexa64"}[sys.platform]
    mex_names = [
        "spikedetector3",
        "mexThSpkPC",
        "mexGetSpikes2",
        "mexMPnu8",
        "mexSVDsmall2",
        "mexWtW2",
        "mexFilterPCs",
        "mexClustering2",
        "mexDistances2",
    ]
    if sorter_name == "kilosort3":
        mex_names.append("spikedetector3PC")
    return all(
        (sorter_path / "CUDA" / f"{name}.{mex_extension}").is_file()
        for name in mex_names
    )


def _set_kilosort_path(sorter_name, sorter_path) -> None:
    """Register the managed installation for this process and its subprocesses."""
    set_sorter_path = {
        "kilosort2_5": Kilosort2_5Sorter.set_kilosort2_5_path,
        "kilosort3": Kilosort3Sorter.set_kilosort3_path,
    }[sorter_name]
    set_sorter_path(sorter_path)
