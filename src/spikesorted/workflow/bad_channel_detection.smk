"""Bad-channel detection per session shank, and the union across sessions."""


def get_bad_channel_detection_input_paths(wildcards):
    """Return the input data files a bad-channel detection job reads.

    Parameters
    ----------
    wildcards
        The job's Snakemake wildcards.

    Returns
    -------
    input_paths
        The session shank's input data files.
    """
    input_paths = []
    for input_path in BadChannelDetectionStep.get_input_paths(
        OUTPUT_PATH, wildcards.session, wildcards.shank
    ):
        input_paths.append(as_pattern(input_path))
    return input_paths


def get_bad_channel_union_input_paths(wildcards):
    """Return every session's bad-channel detection CSV for a union job.

    Parameters
    ----------
    wildcards
        The job's Snakemake wildcards.

    Returns
    -------
    input_paths
        One bad-channel detection CSV per session, for the job's shank.
    """
    input_paths = []
    for input_path in BadChannelUnionStep.get_input_paths(
        OUTPUT_PATH, SESSION_NAMES, wildcards.shank
    ):
        input_paths.append(as_pattern(input_path))
    return input_paths


if "bad_channel_detection" in PIPELINE_CONFIG:

    rule bad_channel_detection:
        input:
            get_bad_channel_detection_input_paths,
        output:
            bad_channel_ids=as_pattern(
                get_bad_channel_ids_filepath(
                    BadChannelDetectionStep.get_output_path(
                        OUTPUT_PATH, "{session}", "{shank}"
                    )
                )
            ),
            bad_channel_labels=as_pattern(
                get_bad_channel_labels_filepath(
                    BadChannelDetectionStep.get_output_path(
                        OUTPUT_PATH, "{session}", "{shank}"
                    )
                )
            ),
        params:
            detection_kwargs=PIPELINE_CONFIG["bad_channel_detection"],
        run:
            BadChannelDetectionStep(
                session_name=wildcards.session,
                shank_id=wildcards.shank,
                config_path=CONFIG_PATH,
                output_path=OUTPUT_PATH,
            ).run()

    if COMBINE_SESSIONS:

        # One job per shank, waiting for that shank in every session.
        rule bad_channel_union:
            input:
                get_bad_channel_union_input_paths,
            output:
                bad_channel_ids=as_pattern(
                    get_bad_channel_ids_filepath(
                        BadChannelUnionStep.get_output_path(OUTPUT_PATH, "{shank}")
                    )
                ),
                sessions=as_pattern(
                    BadChannelUnionStep.get_output_path(OUTPUT_PATH, "{shank}")
                    / "sessions.yaml"
                ),
            params:
                session_names=SESSION_NAMES,
            run:
                BadChannelUnionStep(
                    session_names=SESSION_NAMES,
                    shank_id=wildcards.shank,
                    output_path=OUTPUT_PATH,
                ).run()
