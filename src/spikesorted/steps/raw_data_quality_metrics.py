"""Raw-data quality metrics step."""

import sys
import warnings
from contextlib import redirect_stdout
from dataclasses import dataclass
from typing import ClassVar

from spikeinterface.qualitycontrol import raw_data_quality_metrics

from spikesorted.steps.bad_channel_detection import BadChannelDetectionStep
from spikesorted.steps.base import BasePipelineStep


@dataclass(frozen=True)
class RawDataQualityMetricsStep(BasePipelineStep):
    """Compute and save raw-data quality metrics for each session and shank."""

    _step_name: ClassVar[str] = "raw_data_quality_metrics"

    def run(self, verbose: bool = True) -> None:
        """Remove bad channels and save SI's metric summaries and plots."""
        self.perform_checks()

        bad_channel_detection = BadChannelDetectionStep(
            recordings=self.recordings,
            config_path=self.config_path,
            output_path=self.output_path,
        )
        kwargs = self.config["raw_data_quality_metrics"]

        for (
            session_name,
            shank_id,
            shank_recording,
            shank_path,
        ) in self._get_recordings_and_paths():
            if verbose:
                shank_id_message = f", shank {shank_id}" if shank_id is not None else ""
                print(
                    f"Running raw-data quality metrics for session {session_name}"
                    + shank_id_message,
                    file=sys.stderr,
                    flush=True,
                )

            bad_channel_ids = bad_channel_detection.load_bad_channels(
                session_name, shank_id
            )
            if bad_channel_ids is None:
                warnings.warn(
                    f"No bad channel ids found for session {session_name}, "
                    f"shank {shank_id}. "
                    "Bad channels not removed before raw-data quality metrics.",
                    stacklevel=2,
                )
            elif len(bad_channel_ids) != 0:
                shank_recording = shank_recording.remove_channels(bad_channel_ids)

            with redirect_stdout(sys.stderr):
                raw_data_quality_metrics(
                    shank_recording, folder=shank_path, verbose=verbose, **kwargs
                )

            if verbose:
                print(
                    f"Raw-data quality metrics saved to: {shank_path}",
                    file=sys.stderr,
                    flush=True,
                )

    def perform_checks(self) -> None:
        """Check recordings and protect existing raw-data metrics outputs."""
        super().perform_checks()

        if not self.overwrite:
            for _, _, _, shank_path in self._get_recordings_and_paths():
                if shank_path.exists():
                    raise FileExistsError(
                        "Raw-data quality metrics output folder already exists: "
                        f"{shank_path}. "
                        "Set overwrite=True to replace existing outputs, "
                        "or choose a different output_path."
                    )

    def needs_gpu(self) -> bool:
        """Report whether raw-data quality metrics require a GPU."""
        return False
