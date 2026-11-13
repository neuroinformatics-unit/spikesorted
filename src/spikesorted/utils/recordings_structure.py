"""
The pipeline steps `recordings` can be a fairly complex range of input types:
- a SpikeInterface recording
- a path to a saved SpikeInterface recording
- a dict of SpikeInterface recordings split by shank (e.g. `recordings.split_by("group"))`.
- a tuple of (recording, str) where str is the user-specified name of the session.
For unnamed sessions, ses-001, ses-002, ... are used in input order.
A single unnamed session uses ses-001. Explicit tuple names are preserved.

This is for a single session. For multiple-sessions, these datatypes
are stored in a list (where each element is the recording/s from a single session).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from spikeinterface import load
from spikeinterface.core import BaseRecording

Recording = str | Path | BaseRecording
SessionRecording = Recording | dict[str | int, BaseRecording]
RecordingInput = SessionRecording | tuple[SessionRecording, str]



def get_num_sessions(recordings: RecordingInput | list[RecordingInput]) -> int:
    """Return the number of sessions in the RecordingInput."""
    if isinstance(recordings, list):
        return len(recordings)
    else:
        return 1


def get_path(
    output_path: str | Path, step_name: str,
    session_name: str | None = None, shank_id: str | int | None = None,
) -> Path:
    """Return the output directory for a step, session and shank."""
    step_path = Path(output_path) / step_name
    if session_name is None:
        session_path = step_path
    else:
        session_path = step_path / session_name

    if shank_id is None:
        shank_path = session_path
    else:
        shank_path = session_path / f"shank_{shank_id}"

    return shank_path


def get_recordings_and_paths(
    recordings: RecordingInput | list[RecordingInput],
    output_path: str | Path, step_name: str
) -> list[tuple[str | None, str | int | None, Recording, Path]]:
    """Flatten the RecordingInput so that the recording and output path can be iterated over.

    The function handles every possible RecordingInput type and outputs a
    list of tuples containing (session_name, shank_id, spikeinterface_recording, path).
    This can then be iterated over my steps to quickly process individual
    recordings and store the outputs to the relevant path.
    """
    if isinstance(recordings, list):
        sessions = recordings
    else:
        sessions = [recordings]

    recordings_and_paths = []

    for session_idx, session_recording in enumerate(sessions):

        # Handle the (recording, session_name) case
        if isinstance(session_recording, tuple):
            session_recording, session_name = session_recording
        else:
            session_name = f"ses-{session_idx + 1:03d}"

        # Handle multiple shanks. When only one shank is used, `shank_id`
        # is None and data is not stored in a folder called "shank_<id>".
        for shank_id, recording in iter_over_shanks(session_recording):

            if isinstance(recording, (str, Path)):
                recording = load(recording)

            shank_path = get_path(
                output_path, step_name, session_name, shank_id
            )

            recordings_and_paths.append(
                (session_name, shank_id, recording, shank_path)
            )

    return recordings_and_paths


def get_recordings_and_paths_by_shank(
    recordings: RecordingInput | list[RecordingInput],
    output_path: str | Path, step_name: str
) -> dict[str | int | None, list[tuple[str | None, Recording, Path]]]:
    """Group session names, individual recordings and their output paths by shank id.

    This convenience function is useful when we want to perform actions
    over recordings in the same shanks (e.g. union of bad channel detection).
    """
    recordings_by_shank = {}
    for session_name, shank_id, recording, path in get_recordings_and_paths(
        recordings, output_path, step_name
    ):
        recordings_by_shank.setdefault(shank_id, []).append((session_name, recording, path))

    return recordings_by_shank


def iter_over_shanks(
    recording: SessionRecording,
) -> Iterator[tuple[str | int | None, Recording]]:
    """
    A convenience function to handle that a recording could be
    a single recording dict of {shank_id: recording}.
    """
    if isinstance(recording, dict):
        yield from recording.items()
    else:
        yield None, recording
