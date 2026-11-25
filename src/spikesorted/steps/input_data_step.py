"""Input data step: describe one session shank's recording on disk."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import numpy as np
import yaml
from spikeinterface.core import BaseRecording

from spikesorted.utils.load_recording import load_recording
from spikesorted.utils.output_paths import get_step_output_path


@dataclass(frozen=True)
class InputDataStep:
    """Prepare one session shank's recording for the pipeline's later steps.

    Writes a ``recording.json`` that later steps load and a ``recording_info.yaml``
    describing where the recording came from. Raw data is never copied:
    ``recording.json`` points at the original files. Use ``get_shank_ids()``
    to find which shanks a session's recording has.

    Parameters
    ----------
    recording_path
        Path to the session's recording, in a format ``load_recording`` reads.
    session_name
        Name of the session, used for its output folder.
    shank_id
        Shank to prepare.
    output_path
        The subject folder that all outputs are written below.

    Examples
    --------
    >>> for shank_id in InputDataStep.get_shank_ids("/data/ses-001/recording"):
    ...     InputDataStep(
    ...         recording_path="/data/ses-001/recording",
    ...         session_name="ses-001",
    ...         shank_id=shank_id,
    ...         output_path="/derivatives/sub-001",
    ...     ).run()
    """

    recording_path: str | Path
    session_name: str
    shank_id: str
    output_path: str | Path

    _step_name: ClassVar[str] = "input_data"

    @classmethod
    def get_shank_ids(cls, recording_path: str | Path) -> list[str]:
        """Return the shank IDs of a session's recording.

        Parameters
        ----------
        recording_path
            Path to the session's recording.

        Returns
        -------
        shank_ids
            One ID per ``group``, or ``["0"]`` for a recording without groups.
        """
        recording = load_recording(recording_path)

        return list(_split_by_shank(recording))

    @classmethod
    def get_output_path(
        cls, output_path: str | Path, session_name: str, shank_id: str
    ) -> Path:
        """Return the folder holding a session shank's input data files.

        Parameters
        ----------
        output_path
            The subject folder.
        session_name
            Name of the session.
        shank_id
            Shank ID.

        Returns
        -------
        input_data_path
            The session shank's input data folder.
        """
        return get_step_output_path(output_path, cls._step_name, session_name, shank_id)

    @classmethod
    def get_recording_json_path(
        cls, output_path: str | Path, session_name: str, shank_id: str
    ) -> Path:
        """Return the ``recording.json`` path for a session shank.

        Parameters
        ----------
        output_path
            The subject folder.
        session_name
            Name of the session.
        shank_id
            Shank ID.

        Returns
        -------
        recording_json_path
            Path of the session shank's ``recording.json``.
        """
        return (
            cls.get_output_path(output_path, session_name, shank_id) / "recording.json"
        )

    @classmethod
    def get_recording_info_path(
        cls, output_path: str | Path, session_name: str, shank_id: str
    ) -> Path:
        """Return the ``recording_info.yaml`` path for a session shank.

        Parameters
        ----------
        output_path
            The subject folder.
        session_name
            Name of the session.
        shank_id
            Shank ID.

        Returns
        -------
        recording_info_path
            Path of the session shank's ``recording_info.yaml``.
        """
        return (
            cls.get_output_path(output_path, session_name, shank_id)
            / "recording_info.yaml"
        )

    def run(self) -> None:
        """Write the session shank's ``recording.json`` and ``recording_info.yaml``."""
        recording = load_recording(self.recording_path)

        if recording.get_num_segments() != 1:
            raise ValueError(
                f"Only single-segment recordings are supported; "
                f"session {self.session_name} has "
                f"{recording.get_num_segments()} segments."
            )

        shank_recording = _split_by_shank(recording)[self.shank_id]

        input_data_path = self.get_output_path(
            self.output_path, self.session_name, self.shank_id
        )
        input_data_path.mkdir(parents=True, exist_ok=True)

        shank_recording.dump_to_json(
            self.get_recording_json_path(
                self.output_path, self.session_name, self.shank_id
            ),
            include_properties=True,
        )

        recording_info_path = self.get_recording_info_path(
            self.output_path, self.session_name, self.shank_id
        )
        with recording_info_path.open("w", encoding="utf-8") as file:
            yaml.safe_dump(
                self._get_recording_info(shank_recording), file, sort_keys=False
            )

    def _get_recording_info(self, recording: BaseRecording) -> dict:
        """Describe a shank recording and where it was loaded from.

        Parameters
        ----------
        recording
            The shank's recording.

        Returns
        -------
        recording_info
            The contents of ``recording_info.yaml``.
        """
        channel_ids = recording.get_channel_ids()
        return {
            "session": self.session_name,
            "shank": self.shank_id,
            "recording_path": str(self.recording_path),
            "sampling_frequency": float(recording.get_sampling_frequency()),
            "num_samples": int(recording.get_num_samples()),
            "channel_ids": [str(channel_id) for channel_id in channel_ids],
            "channel_id_dtype": channel_ids.dtype.str,
            "fingerprint": _get_fingerprint(recording),
        }


def _split_by_shank(recording: BaseRecording) -> dict[str, BaseRecording]:
    """Split a recording by its ``group`` property.

    Parameters
    ----------
    recording
        The session's full recording.

    Returns
    -------
    shank_recordings
        Recordings by shank ID. A single-group recording is kept whole under
        its group's ID.
    """
    channel_groups = recording.get_property("group")
    if channel_groups is None:
        # A recording without a probe has no groups, so it is one shank.
        return {"0": recording}

    unique_groups = np.unique(channel_groups)
    if len(unique_groups) == 1:
        return {str(unique_groups[0]): recording}
    else:
        shank_recordings = {}
        for group, shank_recording in recording.split_by("group").items():
            shank_recordings[str(group)] = shank_recording
        return shank_recordings


def _get_fingerprint(recording: BaseRecording) -> str:
    """Hash one second of samples from 10% into a recording.

    Parameters
    ----------
    recording
        The recording to fingerprint.

    Returns
    -------
    fingerprint
        The SHA-256 hex digest of the samples.
    """
    num_samples = recording.get_num_samples()
    start_frame = num_samples // 10
    end_frame = min(start_frame + int(recording.get_sampling_frequency()), num_samples)
    traces = recording.get_traces(start_frame=start_frame, end_frame=end_frame)
    return hashlib.sha256(np.ascontiguousarray(traces).tobytes()).hexdigest()
