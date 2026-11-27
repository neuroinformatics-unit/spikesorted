"""Artifact detection per session shank."""


def get_artifact_detection_input_paths(wildcards):
    """Return the paths an artifact detection job waits for.

    Parameters
    ----------
    wildcards
        The job's Snakemake wildcards.

    Returns
    -------
    input_paths
        The files holding the session shank's bad channels when the config
        includes ``bad_channel_detection``, otherwise its input data files.
    """
    input_paths = []
    for input_path in ArtifactDetectionStep.get_input_paths(
        OUTPUT_PATH, PIPELINE_CONFIG, wildcards.session, wildcards.shank
    ):
        input_paths.append(as_pattern(input_path))
    return input_paths


if "artifact_detection" in PIPELINE_CONFIG:

    rule artifact_detection:
        input:
            get_artifact_detection_input_paths,
        output:
            # The whole folder, so a rerun that finds no artifacts clears the
            # plot of an earlier run.
            directory(
                as_pattern(
                    ArtifactDetectionStep.get_output_path(
                        OUTPUT_PATH, "{session}", "{shank}"
                    )
                )
            ),
        params:
            detection_kwargs=PIPELINE_CONFIG["artifact_detection"],
        run:
            check_bad_channel_union_sessions(wildcards.shank)
            ArtifactDetectionStep(
                session_name=wildcards.session,
                shank_id=wildcards.shank,
                config_path=CONFIG_PATH,
                output_path=OUTPUT_PATH,
            ).run()
