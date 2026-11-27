"""Preprocessing per session shank."""


def get_preprocessing_input_paths(wildcards):
    """Return the paths a preprocessing job waits for.

    Parameters
    ----------
    wildcards
        The job's Snakemake wildcards.

    Returns
    -------
    input_paths
        The session shank's bad channels and artifact detection folder when
        the ``preprocessing`` section has steps that use them, otherwise its
        input data files.
    """
    input_paths = []
    for input_path in PreprocessingStep.get_input_paths(
        OUTPUT_PATH, PIPELINE_CONFIG, wildcards.session, wildcards.shank
    ):
        input_paths.append(as_pattern(input_path))
    return input_paths


rule preprocessing:
    input:
        get_preprocessing_input_paths,
    output:
        directory(
            as_pattern(
                PreprocessingStep.get_output_path(
                    OUTPUT_PATH, "{session}", "{shank}"
                )
            )
        ),
    params:
        # As a list, so reordering the steps counts as a change.
        preprocessing_kwargs=list(PIPELINE_CONFIG["preprocessing"].items()),
    run:
        check_bad_channel_union_sessions(wildcards.shank)
        PreprocessingStep(
            session_name=wildcards.session,
            shank_id=wildcards.shank,
            config_path=CONFIG_PATH,
            output_path=OUTPUT_PATH,
        ).run()
