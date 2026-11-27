"""Bad-channel union step: combine one shank's bad channels across sessions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import ClassVar

import pandas as pd
import yaml

from spikesorted.utils.output_paths import get_step_output_path

from .bad_channel_detection_step import BadChannelDetectionStep
from .utils import get_bad_channel_ids_filepath, save_bad_channel_ids


@dataclass(frozen=True)
class BadChannelUnionStep:
    """Combine one shank's bad channels across sessions.

    Use this when combining sessions (concatenating or unit-matching), which
    needs the same set of channels in every session. It reads each session's
    ``bad_channel_ids.csv`` for the shank and writes their union.

    Outputs use "bad-channels-union" as the session name. A ``sessions.yaml`` beside
    the CSV records the contributing session names and date.

    Parameters
    ----------
    session_names
        The sessions whose bad channels are combined.
    shank_id
        ID of the shank to combine.
    output_path
        The subject folder containing each session's bad-channel outputs.

    Examples
    --------
    >>> BadChannelUnionStep(
    ...     session_names=("ses-001", "ses-002"),
    ...     shank_id="0",
    ...     output_path="/derivatives/sub-001",
    ... ).run()
    """

    session_names: tuple[str, ...]
    shank_id: str
    output_path: str | Path

    _step_name: ClassVar[str] = "bad_channel_detection"

    _union_session_name: ClassVar[str] = "bad-channels-union"

    @classmethod
    def get_input_paths(
        cls,
        output_path: str | Path,
        session_names: tuple[str, ...],
        shank_id: str,
    ) -> list[Path]:
        """Return each session's bad-channel detection CSV for a shank.

        Parameters
        ----------
        output_path
            The subject folder.
        session_names
            The sessions whose bad channels are combined.
        shank_id
            Shank ID.

        Returns
        -------
        session_bad_channel_ids_paths
            One bad-channel detection CSV per session.
        """
        session_bad_channel_ids_paths = []
        for session_name in session_names:
            session_bad_channel_ids_paths.append(
                get_bad_channel_ids_filepath(
                    BadChannelDetectionStep.get_output_path(
                        output_path, session_name, shank_id
                    )
                )
            )
        return session_bad_channel_ids_paths

    @classmethod
    def get_output_path(cls, output_path: str | Path, shank_id: str) -> Path:
        """Return the folder a shank's union is written to.

        Parameters
        ----------
        output_path
            The subject folder.
        shank_id
            Shank ID.

        Returns
        -------
        union_path
            The shank's bad-channel union folder.
        """
        return get_step_output_path(
            output_path, cls._step_name, cls._union_session_name, shank_id
        )

    def run(self) -> None:
        """Read each session's bad channel IDs and save their union."""
        session_bad_channel_ids_paths = self.get_input_paths(
            self.output_path, self.session_names, self.shank_id
        )

        bad_channel_ids: dict[str, str] = {}
        for session_bad_channel_ids_path in session_bad_channel_ids_paths:
            session_bad_channel_ids = pd.read_csv(
                session_bad_channel_ids_path,
                dtype={"channel_id": str},
                keep_default_na=False,
            )
            bad_channel_ids.update(
                zip(
                    session_bad_channel_ids["channel_id"],
                    session_bad_channel_ids["channel_id_dtype"],
                    strict=False,
                )
            )

        union_path = self.get_output_path(self.output_path, self.shank_id)

        union_path.mkdir(parents=True, exist_ok=True)

        sorted_ids = sorted(bad_channel_ids.items())
        save_bad_channel_ids(
            union_path,
            [channel_id for channel_id, _ in sorted_ids],
            [dtype for _, dtype in sorted_ids],
        )
        with (union_path / "sessions.yaml").open("w", encoding="utf-8") as file:
            yaml.safe_dump(
                {
                    "sessions": list(self.session_names),
                    "date": date.today().isoformat(),
                },
                file,
                sort_keys=False,
            )
