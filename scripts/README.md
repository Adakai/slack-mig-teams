## Keep (useful now)

* `create_team_migration.py` — create a Team in **migration** mode (back-in-time).
* `create_channel_migration.py` — add channels in **migration** mode.
* `list_channels.py` — quick sanity check for channels.
* `get_team_state.py` — verifies Group vs Team existence, ops, etc.
* `graph_probe.py` — find exact group(s) and see `resourceProvisioningOptions`.
* `find_team_ids_plus.py` — safer name search (hyphen vs en-dash).
* `recent_teams_fixed.py` — reliable “what Teams exist” listing.
* `poll_team_op.py` — poll long-running ops when Graph returns Location/operation URLs.
* `delete_group.py` — clean up bad attempts.
* `csv_to_mapping.py` — handy if you tweak mappings later.

## Archive

* `create_team_test.py` — superseded by the migration script.
* `create_team_with_owner.py` — not compatible with `creationMode: migration` (and caused the 400).
* `teamify_migration.py` — you saw 405/400; redundant with `create_team_migration.py`.
* `recent_teams.py` — older variant that can 400 without headers; you have the fixed one.
* `token_test.py` — optional; keep only if you like decoding tokens.