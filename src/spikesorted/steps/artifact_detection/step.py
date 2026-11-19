"""Artifact detection step."""

import sys
import warnings
from contextlib import redirect_stdout
from dataclasses import dataclass
from typing import ClassVar

import spikeinterface.preprocessing as spre

from spikesorted.plotting.artifact_detection import save_artifact_plots
from spikesorted.steps.bad_channel_detection.utils import bad_channel_id_loader
from spikesorted.steps.base import BasePipelineStep
from spikesorted.utils.utils import message_user

from .utils import get_artifact_periods_filepath, save_artefact_periods


@dataclass(frozen=True)
class ArtifactDetectionStep(BasePipelineStep):
    """ """

    _step_name: ClassVar[str] = "artifact_detection"

    def run(self, verbose: bool = True) -> None:
        """Detect saturation periods and save sample indices and times in seconds."""
        self.perform_checks()

        saturation_kwargs = self.config["artifact_detection"].get("saturation")

        for (
            session_name,
            shank_id,
            shank_recording,
            shank_path,
        ) in self._get_recordings_and_paths():
            shank_id_message = f", shank {shank_id}" if shank_id else ""
            message_user(
                f"Running artifact detection for session {session_name}"
                + shank_id_message,
                verbose,
            )

            periods_path = get_artifact_periods_filepath(shank_path)
            shank_path.mkdir(parents=True, exist_ok=True)

            # Remove bad channels if they exist
            # TODO: to be moved to check_requirements()
            bad_channel_ids = bad_channel_id_loader(
                self.output_path,
                self.config,
                session_name,
                shank_id,
            )
            if bad_channel_ids is None:
                warnings.warn(
                    f"No bad channel ids found for session {session_name}, "
                    f"shank {shank_id}. "
                    "Bad channels not removed before artifact detection.",
                    stacklevel=2,
                )
            elif len(bad_channel_ids) != 0:
                shank_recording = shank_recording.remove_channels(bad_channel_ids)

            # Perform artefact detection and save the results to CSV
            with redirect_stdout(sys.stderr):
                periods = spre.detect_artifact_periods(
                    shank_recording,
                    method="saturation",
                    method_kwargs=saturation_kwargs,
                )

            save_artefact_periods(shank_path, periods, shank_recording, "SATURATION")

            # Create a plot of a few artefacts and save this to disk.
            save_artifact_plots(shank_recording, periods, shank_path)

            message_user(
                f"Artifact periods saved to: {periods_path}",
                verbose,
            )

    def perform_checks(self) -> None:
        """ """
        super().perform_checks()

        all_kwargs = self.config["artifact_detection"]
        saturation_kwargs = all_kwargs.get("saturation")
        if saturation_kwargs is None:
            raise ValueError("Must pass `saturation` option for artifact detection.")

        envelope_kwargs = all_kwargs.get("envelope")
        if envelope_kwargs:
            raise NotImplementedError(
                "`envelope` option for artifact detection is not currently supported."
            )

        if not self.overwrite:
            for _, _, _, shank_path in self._get_recordings_and_paths():
                if shank_path.exists():
                    raise FileExistsError(
                        "Artifact detection output folder already exists: "
                        f"{shank_path}. "
                        "Set overwrite=True to replace existing outputs, "
                        "or choose a different output_path."
                    )

    def needs_gpu(self) -> bool:
        """Report whether the configured detection method requires a GPU."""
        return False
