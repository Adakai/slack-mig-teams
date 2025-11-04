```markdown
# 🛰️ Slack → Teams Migration Toolkit (`slack-mig-teams`)

A Python-based ETL framework to migrate message history, channels, and structure from **Slack** into **Microsoft Teams** using the [Microsoft Graph Import External Messages API](https://learn.microsoft.com/en-us/microsoftteams/platform/graph-api/import-messages/import-external-messages-to-teams).

> ⚠️ **Important:** Microsoft currently limits imports to *standard channels only* (no private/shared channel imports).  
> Once a team/channel migration is completed, no further message imports are allowed.

---

## 📦 Overview

This project automates the process of extracting Slack data, transforming it to Teams-compatible HTML, and importing it via Microsoft Graph’s `Teamwork.Migrate.All` application permissions.

### **High-level flow**
1. 🧱 **Create Team (migration mode)**  
   → `POST /v1.0/teams` with `@microsoft.graph.teamCreationMode: "migration"`  
2. 📂 **Create Channels (migration mode)**  
   → `POST /teams/{team-id}/channels`  
3. 💬 **Import Messages**  
   → `POST /teams/{team-id}/channels/{channel-id}/messages`  
4. ✅ **Complete Migration**  
   → `POST /teams/{team-id}/channels/{channel-id}/completeMigration`  
   → `POST /teams/{team-id}/completeMigration`  
5. 👥 **Add Members** after completion

---

## 🧰 Environment Setup

### **Prerequisites**
- Windows 11 or later
- Python 3.11+ (via `pyenv`)
- [pipenv](https://pipenv.pypa.io/en/latest/)
- Microsoft 365 tenant with Teams
- App Registration in Azure AD with:
  - **Application permission:** `Teamwork.Migrate.All`
  - **Admin consent granted**

### **Project Structure**
```

slack-mig-teams/
│
├── src/slack2teams/              # ETL core (extract, transform, load)
│   ├── extract/
│   ├── transform/
│   └── load/
│
├── scripts/                      # Helper and test scripts
│   ├── token_test.py
│   ├── create_team_migration.py
│   ├── poll_team_op.py            # (updated) normalizes URLs and prints full request URLs
│   ├── create_channel_migration.py
│   ├── list_channels.py
│   ├── post_test_message.py
│   ├── complete_migration.py
│   ├── get_team_state.py
│   ├── debug_import_one.py        # debug: import a single message and print full response (status/headers/body)
│   ├── inspect_channel.py        # diagnostic: query v1.0 and beta endpoints for team/channel
│   └── decode_token.py           # acquire app token and print decoded JWT claims
│
├── out/                          # Slack export outputs
│   ├── slack_messages.jsonl
│   ├── slack_messages_html.jsonl
│   └── pilot.jsonl
│
├── mapping.json                  # Slack-to-Teams channel/team mapping
├── Pipfile                       # Pipenv dependencies
├── Pipfile.lock
└── README.md                     # ← You are here

````

---

## ⚙️ Initial Setup

```powershell
# 1. Ensure pipenv is ready
pipenv install

# 2. Activate the environment
pipenv shell

# 3. Verify token-based auth
pipenv run python .\scripts\token_test.py
✅ Got app-only token. Expires in (s): 3599
````

### `.env` file (root)

```env
TENANT_ID=<your-tenant-guid>
CLIENT_ID=<your-app-client-id>
CLIENT_SECRET=<your-app-client-secret>
OWNER_UPN=admin@yourdomain.com
```

---

## 🚀 Migration Workflow

### **Step 1: Create Team in Migration Mode**

```powershell
pipenv run python .\scripts\create_team_migration.py
```

✅ Expect `202 Accepted` with headers:

```
Location: /teams/{team-id}/operations/{operation-id}
Content-Location: /teams/{team-id}
```

---

### **Step 2: Poll Until Provisioned**

```powershell
pipenv run python .\scripts\poll_team_op.py "/teams/{team-id}/operations/{operation-id}" "/teams/{team-id}"
```

Wait until:

```
operation status: succeeded
```

---

### **Step 3: Create Channels (Migration Mode)**

```powershell
$teamId = "<TEAM_ID>"
pipenv run python .\scripts\create_channel_migration.py $teamId "General"
pipenv run python .\scripts\create_channel_migration.py $teamId "Announcements"
```

Expected: `202 Accepted`
You can list all channels:

```powershell
pipenv run python .\scripts\list_channels.py $teamId
```

---

### **Step 4: Import Messages**

Your Slack data should already be converted via:

```powershell
pipenv run slack2teams extract-normalized "C:\data\slack-export" out\slack_messages.jsonl
pipenv run slack2teams transform-html "C:\data\slack-export" out\slack_messages.jsonl out\slack_messages_html.jsonl
```

Then test a pilot batch:

```powershell
Get-Content .\out\slack_messages_html.jsonl | Select-Object -First 50 | Set-Content .\out\pilot.jsonl

pipenv run slack2teams load `
  --mapping .\mapping.json `
  --messages .\out\pilot.jsonl `
  --rps 2 `
  --no-dry-run
```

---

### **Step 5: Complete Migration**

```powershell
pipenv run python .\scripts\complete_migration.py <TEAM_ID> <CHANNEL_ID>
```

Expected:

```
channel complete: 204
team complete: 204
```

✅ The team will now appear in **Teams Admin Center** and **Teams Client**.

---

## 🧩 Additional Scripts

| Script                        | Purpose                                              |
| ----------------------------- | ---------------------------------------------------- |
| `get_team_state.py`           | Checks whether a group or team exists, lists ops     |
| `list_team_ops.py`            | Lists ongoing or completed team operations           |
| `create_team_migration.py`    | Creates a migration-mode team with `createdDateTime` |
| `poll_team_op.py`             | Polls long-running operation status                  |
| `create_channel_migration.py` | Creates a migration-mode channel                     |
| `list_channels.py`            | Lists all channels in a given team                   |
| `post_test_message.py`        | Posts a single historical message                    |
| `complete_migration.py`       | Completes both channel + team migrations             |
| `debug_import_one.py`         | Posts one HTML message to the beta import endpoint and prints status/headers/body for debugging |
| `inspect_channel.py`         | Fetches v1.0 and beta team/channel resources and prints headers/body to diagnose state |
| `decode_token.py`            | Acquires app-only token and decodes JWT claims (checks roles like Teamwork.Migrate.All) |

---

## 🧠 Key Notes

* ⚠️ **Private and Shared Channels**: *Not supported* in migration imports.

  * You can import only **standard channels**.
  * After migration completes, you may manually create new private/shared channels for ongoing collaboration.

* 📸 **Inline Images**: Supported through the `hostedContents` API.

* 🔄 **Re-import**: You must **delete the team** and recreate if you need to re-import.

* 🧵 **Threads**: Supported through `replyToId` relationships in messages.

* ⚡ **Rate Limits**: Microsoft Graph throttles imports at ~5 RPS per channel.

## 🐞 Debugging & diagnostics (new)

When an import fails, these scripts help pinpoint the cause quickly:

- `scripts/debug_import_one.py` — posts a single HTML message to the beta import endpoint and prints:
  - full POST URL (beta import endpoint), payload, HTTP status, all response headers and body.
  - Example success shapes: 201 (created) or 202 (accepted with `Location` for operation polling).
  - Example failure shape we observed: 405 with an `UnknownError` and empty message body; the response headers include `request-id` and `client-request-id` which are critical for Microsoft support.

- `scripts/inspect_channel.py` — queries `/v1.0/groups/{team}`, `/v1.0/teams/{team}`, `/v1.0/teams/{team}/channels/{channel}`, and the same channel under `/beta`. Use this to confirm:
  - `resourceProvisioningOptions` includes `"Team"` (teamified group)
  - `membershipType` is `standard` (only standard channels accept imports)

- `scripts/decode_token.py` — acquires the MSAL app-only token and prints decoded JWT claims so you can confirm the token contains the application `roles` (for app-only auth). For example, a working token contained:

```
"roles": [
  "Teamwork.Migrate.All",
  "Group.ReadWrite.All",
  "User.Read.All",
  "ChannelMessage.Read.All"
]
```

If `Teamwork.Migrate.All` is present in `roles` the app has the necessary application permission (admin consent must be granted in Azure).

Common troubleshooting checklist when an import returns 405 / UnknownError

1. Run `inspect_channel.py` and confirm the channel returns `membershipType: "standard"` and the team is teamified.
2. Run `decode_token.py` and confirm the token `roles` includes `Teamwork.Migrate.All`.
3. Run `debug_import_one.py` and capture the full STATUS, HEADERS and BODY. If it returns 202, poll the `Location` operation URL with `poll_team_op.py`.
4. If the debug import returns 405/UnknownError, copy the `request-id` and `client-request-id` from the response headers and include them when contacting Microsoft Support — they can correlate server-side traces.

If you encounter the 405 error and the three diagnostics above are all green (channel standard, token has Teamwork.Migrate.All, fresh debug import still 405), it likely indicates a tenant-level restriction or a transient Graph service-side condition — escalate to Microsoft with the request ids and payload details.

Example: create a fresh debug channel and test

```powershell
$teamId = "<TEAM_ID>"
# create one-off channel for testing
pipenv run python .\scripts\create_channel_migration.py $teamId "pilot-debug-1"
# list channels, then set env
$env:TEAM_ID = $teamId
$env:CHANNEL_ID = "<NEW_CHANNEL_ID>"
pipenv run python .\scripts\debug_import_one.py "Pilot debug message"
```

If the POST returns 201 or 202 the import worked (or is queued). If it returns 405, gather the `request-id` and `client-request-id` and share them with support.

---

## 🧾 Example Mapping File (`mapping.json`)

```json
{
  "teams": [
    {
      "displayName": "PILOT – Jer-nee - MKTG",
      "channels": [
        { "slack_channel": "marketing", "teams_channel": "General" },
        { "slack_channel": "announcements", "teams_channel": "Announcements" }
      ]
    }
  ]
}
```

---

## 🔒 Permissions & Auth

| Permission             | Type        | Description                                          | Consent |
| ---------------------- | ----------- | ---------------------------------------------------- | ------- |
| `Teamwork.Migrate.All` | Application | Create and manage Teams resources for migration      | ✅ Admin |
| `User.Read.All`        | Application | Needed to resolve user IDs for message `from` fields | ✅ Admin |

---

## 🧹 Cleanup / Re-run

If you need to start fresh:

```powershell
# Delete team and associated group
pipenv run python .\scripts\get_team_state.py <TEAM_ID>
# Then remove it manually in the Teams Admin Center or Graph API:
# DELETE https://graph.microsoft.com/v1.0/groups/<TEAM_ID>
```

---

## 🧭 Future Enhancements

* Automate creation/polling/complete steps in one unified command
* Add Slack DM/group chat ingestion to private Teams channels (when Graph supports it)
* Validate HTML sanitization for Slack mrkdwn transformations

---

## 🪄 Credits

Built by **A.T.** with assistance from ChatGPT (DEVBOOT Mode)
Leverages:

* [`requests`](https://pypi.org/project/requests/)
* [`msal`](https://pypi.org/project/msal/)
* [`pipenv`](https://pipenv.pypa.io/)
* [Microsoft Graph API](https://learn.microsoft.com/en-us/graph/api/resources/teams-api-overview)

---

### 🏁 Quick Summary

| Phase            | Command                       | Purpose                        |
| ---------------- | ----------------------------- | ------------------------------ |
| Team Creation    | `create_team_migration.py`    | Build a migration-mode team    |
| Channel Creation | `create_channel_migration.py` | Create migration-mode channels |
| Import Messages  | `slack2teams load`            | Import messages from Slack     |
| Completion       | `complete_migration.py`       | Finalize and make visible      |
| Verification     | `get_team_state.py`           | Check team existence and ops   |

---

**📖 Status:**
Currently validated through pilot team *PILOT – Jer-nee - MKTG* using `Teamwork.Migrate.All` app-only flow.

```
✅ Team provisioned
✅ Channel created
✅ Message import functional
🚧 Multi-channel and full export import pending
```

---

### 🧹 Maintenance & Cleanup

After initial testing or pilot runs, it’s common to have extra Microsoft 365 Groups created during experimentation (for example, a duplicate group with the same display name as your target Team). This section explains how to identify and safely clean those up.

---

#### 🔍 1. Identify orphaned groups

To check for duplicates, use the `graph_probe.py` script:

```powershell
pipenv run python .\scripts\graph_probe.py "PILOT – Jer-nee - MKTG"
```

You’ll see output like:

```
group: PILOT – Jer-nee - MKTG  id:9c3150d9-7444-4fc3-a0ad-92fed93535ca  RPO:[]
group: PILOT – Jer-nee - MKTG  id:5bd96eba-bd59-42b9-8b88-1714d27b3566  RPO:['Team']
```

* The one with **`RPO:['Team']`** is the *real Teams-backed group*.
* Any others with **`RPO:[]`** are orphaned M365 groups that were created by accident during testing.

---

#### 🧽 2. Delete an orphan group

Use the `delete_group.py` script to remove it permanently.

```powershell
# Save script
@'
import os, sys, requests
from msal import ConfidentialClientApplication

GRAPH="https://graph.microsoft.com"; API=f"{GRAPH}/v1.0"

if len(sys.argv) < 2:
    raise SystemExit("Usage: python delete_group.py <GROUP_ID>")
gid = sys.argv[1]

app = ConfidentialClientApplication(
    os.getenv("CLIENT_ID"),
    authority=f"https://login.microsoftonline.com/{os.getenv('TENANT_ID')}",
    client_credential=os.getenv("CLIENT_SECRET"),
)
tok = app.acquire_token_for_client(scopes=[f"{GRAPH}/.default"])
if "access_token" not in tok:
    raise SystemExit(f"Token failure: {tok}")

h = {"Authorization": f"Bearer {tok['access_token']}"}

# Optional: confirm group info before delete
g = requests.get(f"{API}/groups/{gid}?$select=id,displayName", headers=h, timeout=60)
print("GET /groups =>", g.status_code, g.text[:200])

# Delete it
r = requests.delete(f"{API}/groups/{gid}", headers=h, timeout=60)
print("DELETE /groups =>", r.status_code or 204)
'@ | Set-Content -Encoding utf8 .\scripts\delete_group.py

# Run it (replace with the orphaned group ID)
pipenv run python .\scripts\delete_group.py 9c3150d9-7444-4fc3-a0ad-92fed93535ca
```

✅ **Expected output:**

```
GET /groups => 200 ...
DELETE /groups => 204
```

---

#### ✏️ 3. (Optional) Rename instead of deleting

If you’re not ready to delete it yet, rename it to avoid confusion:

```powershell
@'
import os, sys, requests
from msal import ConfidentialClientApplication

GRAPH="https://graph.microsoft.com"; API=f"{GRAPH}/v1.0"

gid=sys.argv[1]
app=ConfidentialClientApplication(
    os.getenv("CLIENT_ID"),
    authority=f"https://login.microsoftonline.com/{os.getenv('TENANT_ID')}"),
    client_credential=os.getenv("CLIENT_SECRET"))
tok=app.acquire_token_for_client(scopes=[f"{GRAPH}/.default"])
h={"Authorization":f"Bearer {tok['access_token']}", "Content-Type":"application/json"}

r=requests.patch(f"{API}/groups/{gid}", headers=h,
                 json={"displayName":"PILOT – Jer-nee - MKTG (orphan)"},
                 timeout=60)
print("PATCH /groups =>", r.status_code, r.text)
'@ | Set-Content -Encoding utf8 .\scripts\rename_group.py

pipenv run python .\scripts\rename_group.py 9c3150d9-7444-4fc3-a0ad-92fed93535ca
```

---

#### 🧠 4. Verify team state

If you’re not sure which group is teamified, run:

```powershell
pipenv run python .\scripts\get_team_state.py $teamId
```

You’ll get a summary like:

```
GET /groups/{id} => 200
GET /groups/{id}/team => 200 (team exists)
GET /teams/{id}/operations => 200
ops: []
```

If `/groups/{id}/team` is **404**, that group isn’t a real Team.

---

#### 🧩 5. Token validation (for troubleshooting)

If any Graph script fails with a token or permission error, re-run your token test:

```powershell
pipenv run python .\scripts\token_test.py
```

✅ Output example:

```
✅ Got app-only token. Expires in (s): 3599
```

If it fails, double-check `.env` for:

```
TENANT_ID=
CLIENT_ID=
CLIENT_SECRET=
OWNER_UPN=
```

…and verify your app registration includes:

* `Teamwork.Migrate.All`
* `Group.ReadWrite.All`
* `User.Read.All`
  (all as **Application permissions** with **Admin consent** granted)

---

#### 🚨 6. Cleanup notes

* Deleting an M365 group **permanently removes** its mailbox, SPO site, and membership.
* Orphaned groups will **not appear** in Teams unless explicitly teamified.
* Always verify the correct ID using `graph_probe.py` before deletion.
* The valid team ID for this project (as of last successful migration) is:

  ```
  5bd96eba-bd59-42b9-8b88-1714d27b3566
  ```

---

Would you like me to extend this README block further with a **“Recovery & Verification”** section (how to restore deleted groups or verify SPO sites via Graph)?
It’s useful for admin-level troubleshooting if something gets removed accidentally.


> “Importing history means preserving context — not just messages.”
> — *A.T. (2025)*