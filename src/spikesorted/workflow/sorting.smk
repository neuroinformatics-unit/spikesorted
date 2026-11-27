"""Spike sorting per session shank, or per shank when sessions are combined."""

if COMBINE_SESSIONS:
    # Sessions are sorted together, as the combined recording.
    SORTED_SESSION_NAMES = (CombineSessionsStep.combined_session_name,)
else:
    SORTED_SESSION_NAMES = SESSION_NAMES


def get_sorting_input_paths(wildcards):
    """Return the folder a sorting job waits for.

    Parameters
    ----------
    wildcards
        The job's Snakemake wildcards.

    Returns
    -------
    input_paths
        The shank's combine sessions folder when sessions are combined,
        otherwise the session shank's preprocessing folder.
    """
    input_paths = []
    for input_path in SortingStep.get_input_paths(
        OUTPUT_PATH, PIPELINE_CONFIG, wildcards.session, wildcards.shank
    ):
        input_paths.append(as_pattern(input_path))
    return input_paths


rule sorting:
    input:
        get_sorting_input_paths,
    output:
        directory(
            as_pattern(
                SortingStep.get_output_path(OUTPUT_PATH, "{session}", "{shank}")
            )
        ),
    wildcard_constraints:
        session="|".join(re.escape(name) for name in SORTED_SESSION_NAMES),
    params:
        sorting_kwargs=PIPELINE_CONFIG["sorting"],
    run:
        SortingStep(
            session_name=wildcards.session,
            shank_id=wildcards.shank,
            config_path=CONFIG_PATH,
            output_path=OUTPUT_PATH,
        ).run()
