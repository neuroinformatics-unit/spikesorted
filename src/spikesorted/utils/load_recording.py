"""Open a session's recording from its path, working out the file format."""

from __future__ import annotations

import sys
from contextlib import redirect_stdout
from pathlib import Path

import spikeinterface.extractors as se
from spikeinterface import load
from spikeinterface.core import BaseRecording

_SPIKEINTERFACE_SUFFIXES = (".json", ".pkl", ".pickle")


def load_recording(recording_path: str | Path) -> BaseRecording:
    """Open a recording saved by SpikeInterface, SpikeGLX or Open Ephys.

    The format is worked out from the path:

    - SpikeInterface: a ``.json`` or ``.pkl`` dump, or a folder saved with
      ``recording.save()``.
    - SpikeGLX: an ``*.imec<N>.ap.bin`` file, or a folder containing one. The
      AP stream is used.
    - Open Ephys: a folder containing a ``Record Node`` folder or a
      ``structure.oebin`` file. The AP stream is used when there are several.

    Parameters
    ----------
    recording_path
        Path to the recording.

    Returns
    -------
    recording
        The recording, which still reads from the original files.

    Examples
    --------
    >>> recording = load_recording("/data/sub-001/ses-001/ephys/run_g0")
    """
    recording_path = Path(recording_path)

    with redirect_stdout(sys.stderr):
        if _is_spikeinterface_recording(recording_path):
            return load(recording_path)

        if _is_spikeglx_recording(recording_path):
            return _read_spikeglx(recording_path)

        if _is_openephys_recording(recording_path):
            return _read_openephys(recording_path)

    raise ValueError(
        f"Cannot work out the recording format of {recording_path}. Supported "
        "formats are a SpikeInterface .json/.pkl dump or saved folder, a "
        "SpikeGLX *.imec<N>.ap.bin file or folder, and an Open Ephys folder."
    )


def _is_spikeinterface_recording(recording_path: Path) -> bool:
    """Return whether a path is a SpikeInterface dump or saved folder.

    Parameters
    ----------
    recording_path
        Path to the recording.

    Returns
    -------
    is_spikeinterface_recording
        Whether ``spikeinterface.load`` can open the path.
    """
    if recording_path.suffix in _SPIKEINTERFACE_SUFFIXES:
        return True
    return (recording_path / "si_folder.json").is_file()


def _is_spikeglx_recording(recording_path: Path) -> bool:
    """Return whether a path is a SpikeGLX AP file or a folder containing one.

    Parameters
    ----------
    recording_path
        Path to the recording.

    Returns
    -------
    is_spikeglx_recording
        Whether the path holds a SpikeGLX ``*.imec<N>.ap.bin`` file.
    """
    if recording_path.is_file():
        return _is_spikeglx_ap_file(recording_path)
    return any(_is_spikeglx_ap_file(path) for path in recording_path.rglob("*.bin"))


def _is_spikeglx_ap_file(file_path: Path) -> bool:
    """Return whether a file is a SpikeGLX AP binary, e.g. ``run_g0_t0.imec0.ap.bin``.

    Parameters
    ----------
    file_path
        The file to check.

    Returns
    -------
    is_spikeglx_ap_file
        Whether the file name has an ``imec`` probe and the ``ap`` stream.
    """
    name_parts = file_path.name.split(".")
    return (
        len(name_parts) >= 3
        and name_parts[-1] == "bin"
        and name_parts[-2] == "ap"
        and name_parts[-3].startswith("imec")
    )


def _read_spikeglx(recording_path: Path) -> BaseRecording:
    """Read the AP stream of a SpikeGLX recording.

    Parameters
    ----------
    recording_path
        A SpikeGLX AP file, or a folder containing the recording.

    Returns
    -------
    recording
        The AP stream.
    """
    if recording_path.is_file():
        # e.g. run_g0_t0.imec0.ap.bin is stream "imec0.ap" of its folder.
        name_parts = recording_path.name.split(".")
        stream_id = f"{name_parts[-3]}.{name_parts[-2]}"
        return se.read_spikeglx(recording_path.parent, stream_id=stream_id)

    _, stream_ids = se.get_neo_streams("spikeglx", recording_path)
    stream_id = _get_ap_stream(recording_path, stream_ids, ".ap")
    return se.read_spikeglx(recording_path, stream_id=stream_id)


def _is_openephys_recording(recording_path: Path) -> bool:
    """Return whether a path is an Open Ephys recording folder.

    Parameters
    ----------
    recording_path
        Path to the recording.

    Returns
    -------
    is_openephys_recording
        Whether the folder contains a ``Record Node`` folder or a
        ``structure.oebin`` file.
    """
    if not recording_path.is_dir():
        return False
    if any(recording_path.rglob("structure.oebin")):
        return True
    return any(recording_path.rglob("Record Node*"))


def _read_openephys(recording_path: Path) -> BaseRecording:
    """Read the AP stream of an Open Ephys recording.

    Parameters
    ----------
    recording_path
        The Open Ephys recording folder.

    Returns
    -------
    recording
        The only stream, or the AP stream when there are several.
    """
    stream_names, _ = se.get_neo_streams("openephysbinary", recording_path)
    if len(stream_names) == 1:
        return se.read_openephys(recording_path, stream_name=stream_names[0])

    stream_name = _get_ap_stream(recording_path, stream_names, "-AP")
    return se.read_openephys(recording_path, stream_name=stream_name)


def _get_ap_stream(
    recording_path: Path, stream_names: list[str], ap_suffix: str
) -> str:
    """Return the one stream whose name ends with the AP suffix.

    Parameters
    ----------
    recording_path
        Path to the recording, for the error message.
    stream_names
        The recording's stream names or IDs.
    ap_suffix
        The ending that marks an AP stream, e.g. ``".ap"`` or ``"-AP"``.

    Returns
    -------
    stream_name
        The AP stream.
    """
    ap_stream_names = [name for name in stream_names if name.endswith(ap_suffix)]
    if len(ap_stream_names) != 1:
        raise ValueError(
            f"Expected one AP stream in {recording_path}, but found "
            f"{ap_stream_names} (all streams: {stream_names}). Recordings with "
            "several probes are not supported yet."
        )
    return ap_stream_names[0]
