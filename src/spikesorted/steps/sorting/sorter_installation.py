"""Install MATLAB Kilosort revisions for use with SpikeInterface."""

import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal
from urllib.request import urlretrieve
from zipfile import ZipFile

from spikeinterface.sorters import (
    Kilosort2_5Sorter,
    Kilosort3Sorter,
    installed_sorters,
)


def get_sorter_installation_path(
    sorter_name: Literal["kilosort2_5", "kilosort3"],
) -> Path:
    """Return the shared location used to install and discover the sorter."""
    return Path.home() / ".spikesorted" / "sorters" / sorter_name


def install_kilosort(
    sorter_name: Literal["kilosort2_5", "kilosort3"],
) -> Path:
    """Download a pinned commit, build its MEX files, and register its path.

    MATLAB must be on PATH. MATLAB needs a configured CUDA/C++ compiler
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
        raise FileNotFoundError(
            f"Cannot install {sorter_name}. "
            "MATLAB is not installed or is not available on PATH."
        )

    matlab_command = [matlab]
    if sys.platform == "win32":
        matlab_command.append("-wait")

    sorter_path = get_sorter_installation_path(sorter_name)
    with TemporaryDirectory() as download_folder:
        download_path = Path(download_folder)
        archive_path = download_path / "kilosort.zip"
        urlretrieve(
            f"https://github.com/MouseLand/Kilosort/archive/{commit}.zip",
            archive_path,
        )
        with ZipFile(archive_path) as archive:
            archive.extractall(download_path)
        shutil.copytree(
            download_path / f"Kilosort-{commit}",
            sorter_path,
            dirs_exist_ok=True,
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


def ensure_sorter_installed(sorter_name: str) -> None:
    """Check the configured sorter is installed, installing MATLAB Kilosort if not.

    Run by the ``spikesorted`` command before any job starts, on the machine
    the command is launched from. ``kilosort2_5`` and ``kilosort3`` are
    downloaded and built when missing. Any other sorter must already be
    installed in the environment.

    Parameters
    ----------
    sorter_name
        Name of the sorter in the config's ``sorting`` section.
    """
    if sorter_name == "kilosort2_5":
        ensure_kilosort_installed("kilosort2_5")
    elif sorter_name == "kilosort3":
        ensure_kilosort_installed("kilosort3")
    elif sorter_name not in installed_sorters():
        raise RuntimeError(
            f"The sorter {sorter_name!r} is not installed. Install it in this "
            "environment before running the pipeline."
        )


def register_installed_kilosort(
    sorter_name: Literal["kilosort2_5", "kilosort3"],
) -> None:
    """Register an already-built Kilosort installation with SpikeInterface.

    Used by the sorting step, which runs in its own process and so registers
    the path itself. It does not install the sorter.

    Parameters
    ----------
    sorter_name
        The MATLAB Kilosort version to register.
    """
    sorter_path = get_sorter_installation_path(sorter_name)
    if not (sorter_path.is_dir() and _has_kilosort_mex_files(sorter_name, sorter_path)):
        raise FileNotFoundError(
            f"{sorter_name} is not installed at {sorter_path}. Run the pipeline "
            "with the `spikesorted` command, which installs it before starting."
        )
    _set_kilosort_path(sorter_name, sorter_path)


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
