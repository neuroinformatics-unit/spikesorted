"""Recording input type aliases."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from spikeinterface.core import BaseRecording

    Recording: TypeAlias = str | Path | BaseRecording
    SessionRecording: TypeAlias = Recording | dict[str | int, BaseRecording]
    RecordingInput: TypeAlias = SessionRecording | tuple[SessionRecording, str]
