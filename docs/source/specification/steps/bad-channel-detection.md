# Bad-channel detection

## Outputs

### `BAD_CHANNEL_IDS`

The channel IDs identified as bad by the detect-bad-channels step.

Saved as `bad_channel_ids.csv`, with one row per detected bad channel:

| Column | Contents |
| --- | --- |
| `channel_id` | The channel identifier from the input recording. |

If no bad channels are detected, the file contains only the `channel_id` header.

### `BAD_CHANNEL_LABELS`

The bad-channel classification associated with each `BAD_CHANNEL_ID`.

Saved as `bad_channel_labels.csv`, with one row for **every channel** in the input recording, including good channels, in recording channel order:

| Column | Contents |
| --- | --- |
| `channel_id` | The channel identifier from the input recording. |
| `label` | The classification returned by the configured SpikeInterface bad-channel detection method. |

Both files include a header row and are written without a DataFrame index column. A separate pair is saved for each session and shank processed by the step.
