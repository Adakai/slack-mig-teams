 - src/slack2teams/transform/slack_to_html.py — Slack mrkdwn → HTML conversion. Mentions are resolved to @name and channel links are converted to hash-prefixed names (for example: #general) before markdown rendering.

Quick architecture summary (what to know):

- Flow: Extract Slack export → normalize messages (`extract-normalized`) → convert mrkdwn to HTML (`transform-html`) → load using mapping (`load` / `load_with_mapping`) which creates teams/channels (migration mode), imports messages per-channel using the beta `messages/import` endpoint, then optionally completes channels and teams.
- Mapping: `mapping.json` maps Slack channel names to Teams team display names and channel display names. `load_with_mapping` builds a reverse index from `slack` → (team, channel, type).
- Throttling: The loader uses a simple per-channel rate (CLI default `rps=4.0`) — keep ≤5 RPS to avoid throttling.

Common failure points (what an assistant should check first):

1. Environment / Auth
   - The code uses app-only auth (MSAL ConfidentialClientApplication). Ensure `TENANT_ID`, `CLIENT_ID`, `CLIENT_SECRET` are present in env or `.env` and that the app has `Teamwork.Migrate.All` and `User.Read.All` as application permissions with admin consent.
   - Token failures typically raise a `RuntimeError` or an assertion in scripts (check `token` contents printed by `scripts/token_test.py`).

2. Migration mode requirements
   - `createdDateTime` must be provided and be in the past for migration-mode team/channel creation. The scripts set `created = "2024-01-02T12:00:00Z"` by default; keep a past timestamp.
   - Some tenants return `202` with operation URLs. Use `scripts/poll_team_op.py` to poll the operation URL (first arg) and then fetch the created team (second arg). The loader contains logic to poll operation-location headers; scripts do the same.

3. Message import errors
   - Imports use the beta endpoint: `https://graph.microsoft.com/beta/teams/{team}/channels/{channel}/messages/import`. Errors returned here are often more descriptive. To reproduce, use `scripts/debug_import_one.py` which prints status, headers and body.
   - Common responses:
     - 405 / 409: wrong endpoint, channel not in migration mode, or incorrect membershipType.
     - 403/401: token scopes/consent issue.
     - 429: throttling — reduce `rps` and add retries/backoff.

4. Channel types and visibility
   - Teams migration only supports standard channels for message imports. Private/shared channels are not supported by import APIs. Check `mapping.json` and ensure `type: "standard"` for channels you import.

Project-specific patterns and conventions

- The code favors small, imperative scripts in `scripts/` for provisioning tasks. Use them when experimenting (they print full responses).
- The loader keeps `dry_run=True` default behavior to preview payloads — set `--no-dry-run` or call `load` with `dry_run=False` to actually call Graph.
- Slack-to-Teams transformations happen in two steps: normalization (JSONL with text_raw) then HTML transform (adds `text_html`). The loader prefers `text_html` but falls back to `text_raw`.

Examples to show when editing or creating PRs

- Reproducing an import error locally (PowerShell):

```powershell
$env:TENANT_ID = "<your-tenant>"
$env:CLIENT_ID = "<client id>"
$env:CLIENT_SECRET = "<secret>"
$env:TEAM_ID = "<team-id>"
$env:CHANNEL_ID = "<channel-id>"
pipenv run python .\scripts\debug_import_one.py "Test import"
```

- Create team + channel (migration mode) then poll:

```powershell
pipenv run python .\scripts\create_team_migration.py
# Copy Location header -> $opurl
pipenv run python .\scripts\poll_team_op.py $opurl "/teams/{team-id}"
pipenv run python .\scripts\create_channel_migration.py <team-id> "General"
```

When to avoid making changes

- Don’t change the `createdDateTime` generation to a future date — Graph rejects migration teams with future timestamps.
- Don’t attempt to import into private/shared channels — Graph will return unhelpful errors.

Where to look for more context

- `README.md` — authoritative workflow, environment setup and mapping examples.
- `scripts/README.md` — notes about which scripts are current vs archived.
- `src/slack2teams/load/graph_loader.py` — the single file that contains most Graph interactions. When debugging imports, search this file for `import` and `completeMigration` calls.

If something is missing or unclear in these instructions, ask for the specific failing HTTP response (status + headers + body) captured by `scripts/debug_import_one.py` and I will suggest next steps (fix headers, token scope, channel state, or payload). 
