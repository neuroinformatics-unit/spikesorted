"""Input data: the first step, run once per session shank.

Opens the recording path given for the session with ``load_recording``
(SpikeGLX, Open Ephys or a SpikeInterface dump) and writes two files to
``<session>/ephys/shank-<id>/input_data/``:

- ``recording.json``: the shank's recording as a SpikeInterface JSON dump.
  It points at the original data files and selects the shank's channels;
  no data is copied. Every later step loads its recording from this file.
- ``recording_info.yaml``: a short, readable summary of the recording (the
  path it was loaded from, sampling frequency, number of samples, channel IDs
  and a fingerprint of the data), for checking by hand which recording a
  session was built from. No step reads it.

The job reruns when the session's recording path changes or its data is
newer than these files, and everything downstream of the shank reruns with it.
"""


rule input_data:
    input:
        lambda wildcards: RECORDING_PATHS[wildcards.session],
    output:
        recording_json=as_pattern(
            InputDataStep.get_recording_json_path(
                OUTPUT_PATH, "{session}", "{shank}"
            )
        ),
        recording_info=as_pattern(
            InputDataStep.get_recording_info_path(OUTPUT_PATH, "{session}", "{shank}")
        ),
    run:
        InputDataStep(
            recording_path=RECORDING_PATHS[wildcards.session],
            session_name=wildcards.session,
            shank_id=wildcards.shank,
            output_path=OUTPUT_PATH,
        ).run()
