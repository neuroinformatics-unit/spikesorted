# Bad-channel detection

Bad channel detection outputs are stored in the
subject, session or shank folder of the `bad_channel_detection` folder.

If multiple sessions are passed and `combine_sessions` is included in the Config
file, the union of bad channels across sessions is also saved for each shank.

## Outputs

### `BAD_CHANNEL_IDS`

The channel IDs identified as bad by the detect-bad-channels step.

Saved as `bad_channel_ids.csv`, with one row per detected bad channel:

| Column | Contents |
| --- | --- |
| `channel_id` | The channel identifier from the input recording. |

If no bad channels are detected, the file contains only the `channel_id` header.

### `BAD_CHANNEL_LABELS`

The classification associated with each channel ID.

Saved as `bad_channel_labels.csv`, with one row for every channel in the input recording:

| Column | Contents |
| --- | --- |
| `channel_id` | The channel identifier from the input recording. |
| `label` | The classification returned by the configured SpikeInterface bad-channel detection method. |

If no bad channels are detected, the file still contains every channel, each labeled `good`.

### Bad channels union

The union of all bad channels detected across included sessions. It defines a 
shared set of bad channels across the sessions being combined.

The bad channel unions are saved under
`bad_channel_detection/session_unions/shank_<shank_id>/`.
The shank folder is omitted when recordings are not split by shank.

| File | Contents |
| --- | --- |
| `bad_channel_ids.csv` | One `channel_id` column, with one row per unique bad channel ID across the sessions. |
| `sessions.yaml` | A `sessions` list naming the contributing sessions and a `date` field recording the generation date as `YYYY-MM-DD`. |

If no bad channels are detected in any session, the union CSV contains only
the `channel_id` header. 
