"""File loading and path helpers for bad channel detection."""

from pathlib import Path

import pandas as pd

from spikesorted.utils.output_paths import get_step_output_path
from spikesorted.utils.utils import message_user


# TODO: move this stuff into self._check_dependecy() function for each
# step, see https://github.com/neuroinformatics-unit/spikesorted/issues/24
def load_and_check_bad_channel_ids(
    output_path,
    config,
    session_name,
    shank_id=None,
    required=False,
    verbose=False,
):
    """Load session or union bad-channel IDs in their original dtype.

    combine_sessions selects the union for the shank. Missing files return
    None unless required is True, in which case FileNotFoundError is raised.
    """
    combine_sessions = "combine_sessions" in config
    union_path = get_bad_channel_ids_filepath(
        get_step_output_path(
            output_path,
            "bad_channel_detection",
            "bad-channels-union",
            shank_id,
        )
    )
    # TODO: move this stuff into self._check_dependecy() function for each
    # step, see https://github.com/neuroinformatics-unit/spikesorted/issues/24
    if combine_sessions:
        channel_ids_path = union_path
    else:
        channel_ids_path = get_bad_channel_ids_filepath(
            get_step_output_path(
                output_path,
                "bad_channel_detection",
                session_name,
                shank_id,
            )
        )

    if not channel_ids_path.exists():
        if required:
            raise FileNotFoundError(
                f"Required bad-channel CSV missing for session {session_name!r}, "
                f"shank {shank_id!r}: {channel_ids_path}. "
                "Run bad-channel detection for this session/shank first."
            )
        return None

    message_user(
        f"Loading bad channels from: {channel_ids_path}",
        verbose,
    )
    bad_channels = pd.read_csv(channel_ids_path, dtype={"channel_id": str})

    bad_channel_ids = bad_channels["channel_id"].to_numpy()

    if not bad_channels.empty:
        # Bad channels can be str or int dtype
        bad_channels_type = bad_channels["channel_id_dtype"].iloc[0]
        bad_channel_ids = bad_channel_ids.astype(bad_channels_type)

    return bad_channel_ids


def get_bad_channel_ids_filepath(shank_path: Path) -> Path:
    """Return the bad-channel IDs CSV path for a shank output directory."""
    return shank_path / "bad_channel_ids.csv"


def get_bad_channel_labels_filepath(shank_path: Path) -> Path:
    """Return the all-channel labels CSV path for a shank output directory."""
    return shank_path / "bad_channel_labels.csv"


def save_bad_channel_ids(shank_path, bad_channel_ids, channel_id_dtype):
    """Save IDs with a shared dtype or a dtype per ID for a session union."""
    bad_ids_df = pd.DataFrame(
        {
            "channel_id": bad_channel_ids,
            "channel_id_dtype": channel_id_dtype,
        }
    )
    bad_ids_df.to_csv(get_bad_channel_ids_filepath(shank_path), index=False)


def save_bad_channel_labels(shank_path, channel_ids, channel_labels, channel_id_dtype):
    """Save all channel IDs, their labels and original dtype."""
    labels_df = pd.DataFrame(
        {
            "channel_id": channel_ids,
            "label": channel_labels,
            "channel_id_dtype": channel_id_dtype,
        }
    )
    labels_df.to_csv(get_bad_channel_labels_filepath(shank_path), index=False)
