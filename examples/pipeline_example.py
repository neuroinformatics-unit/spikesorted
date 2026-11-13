"""Run bad-channel and artifact detection on the local Neuropixels test recording."""

from datetime import datetime
from pathlib import Path
import sys
from spikesorted.pipeline.pipeline import Pipeline
from spikesorted.utils.testing_utils import get_test_data


def main():

    repo_path = Path(__file__).resolve().parents[1]
    recording = get_test_data(repo_path)
    run_name = f"{datetime.now():%Y-%m-%d_%H-%M-%S_%f}_{Path(__file__).stem}"
    output_path = repo_path / "examples" / "outputs" / run_name

    Pipeline(
        recordings=recording,
        config_path=repo_path / "examples/full_pipeline_test_config.yaml",
        output_path=output_path,
        stop_after_step="artifact_detection",
        overwrite=False,
    ).run()

    print(f"Results saved to: {output_path}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
