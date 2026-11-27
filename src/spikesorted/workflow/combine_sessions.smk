"""Combine each shank's preprocessed sessions."""


def get_combine_sessions_input_paths(wildcards):
    """Return every session's preprocessing folder for a combine sessions job.

    Parameters
    ----------
    wildcards
        The job's Snakemake wildcards.

    Returns
    -------
    input_paths
        One preprocessing folder per session, for the job's shank.
    """
    input_paths = []
    for input_path in CombineSessionsStep.get_input_paths(
        OUTPUT_PATH, SESSION_NAMES, wildcards.shank
    ):
        input_paths.append(as_pattern(input_path))
    return input_paths


if COMBINE_SESSIONS:

    # One job per shank, waiting for that shank in every session.
    rule combine_sessions:
        input:
            get_combine_sessions_input_paths,
        output:
            directory(
                as_pattern(
                    CombineSessionsStep.get_output_path(OUTPUT_PATH, "{shank}")
                )
            ),
        params:
            session_names=SESSION_NAMES,
            combine_kwargs=PIPELINE_CONFIG["combine_sessions"],
        run:
            CombineSessionsStep(
                session_names=SESSION_NAMES,
                shank_id=wildcards.shank,
                config_path=CONFIG_PATH,
                output_path=OUTPUT_PATH,
            ).run()
