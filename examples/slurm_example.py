from datetime import datetime
from pathlib import Path

from spikesorted.slurm.slurm_for_pipeline import run_pipeline_with_slurm
from spikesorted.utils.testing_utils import get_test_data


def main():
    repo_path = Path(__file__).resolve().parents[1]

    recordings = [get_test_data(repo_path)]

    run_name = f"{datetime.now():%Y-%m-%d_%H-%M-%S_%f}_{Path(__file__).stem}"
    output_path = repo_path / "examples" / "outputs" / run_name

    job = run_pipeline_with_slurm(
        recordings=recordings,
        config_path=repo_path / "examples/full_pipeline_test_config.yaml",
        output_path=output_path,
        overwrite=False,
        num_cores=1,
        slurm_opts={
            "conda_env_name": "spikesorted",  # Change to your Conda environment.
            "matlab_module_name": None,  # Set your cluster's MATLAB module if needed.
            "slurm_partition": "cpu",  # Change to your cluster's partition.
            "mem_gb": 4,
            "timeout_min": 10,
            "slurm_array_parallelism": 4,
        },
        coordinator_slurm_opts={
            "conda_env_name": "spikesorted",
            "slurm_partition": "cpu",
            "mem_gb": 4,
            "timeout_min": 1440,  # Includes time waiting for workers to start.
        },
    )
    print(f"Coordinator job submitted: {job.job_id}")
    print(f"Results and SLURM logs: {output_path}")
    # Uncomment to wait for completion and propagate worker errors.
    # job.result()


if __name__ == "__main__":
    main()
