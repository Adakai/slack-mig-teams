# from __future__ import annotations

# GRAPH = "https://graph.microsoft.com"
# API   = f"{GRAPH}/v1.0"
# GRAPH_BETA = f"{GRAPH}/beta"
# import os
# def _default_created_iso():
#     # Allow override via env (e.g., TEAM_CREATED_ISO=2024-01-02T12:00:00Z)
#     return os.getenv("TEAM_CREATED_ISO") or "2024-01-02T12:00:00Z"
# import os
# import json
# import time
# from pathlib import Path
# from typing import Dict, Iterable, Optional, List
# import requests
# from msal import ConfidentialClientApplication

# #GRAPH = "https://graph.microsoft.com/v1.0"



# # -------- Auth helpers --------
# def _get_token() -> str:
#     tenant = os.getenv("TENANT_ID")
#     client_id = os.getenv("CLIENT_ID")
#     client_secret = os.getenv("CLIENT_SECRET")
#     if not all([tenant, client_id, client_secret]):
#         raise RuntimeError(
#             "Missing TENANT_ID / CLIENT_ID / CLIENT_SECRET in env (.env)."
#         )
#     app = ConfidentialClientApplication(
#         client_id=client_id,
#         client_credential=client_secret,
#         authority=f"https://login.microsoftonline.com/{tenant}",
#     )
#     res = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
#     if "access_token" not in res:
#         raise RuntimeError(f"Token failure: {res}")
#     return res["access_token"]


# def _headers(tok: str) -> Dict[str, str]:
#     return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


# # -------- Team / Channel creation (migration mode) --------
# def create_team_migration(
#     display_name: str,
#     description: str = "",
#     created_iso: Optional[str] = None,
#     dry_run=False,
# ) -> str:
#     """
#     Create a Team in migration mode. Returns teamId.
#     """
#     payload = {
#         "@microsoft.graph.teamCreationMode": "migration",
#         "template@odata.bind": f"{GRAPH}/teamsTemplates('standard')",
#         "displayName": display_name,
#         "description": description,
#     }
#     if created_iso:
#         payload["createdDateTime"] = created_iso

#     if dry_run:
#         print(
#             "DRY-RUN create team payload:",
#             json.dumps(payload, ensure_ascii=False)[:500],
#         )
#         return f"DRY_RUN_TEAM_{display_name}"

#     tok = _get_token()
#     r = requests.post(
#         f"{GRAPH}/teams", headers=_headers(tok), data=json.dumps(payload), timeout=120
#     )
#     if r.status_code not in (201, 202):
#         raise RuntimeError(f"Create team failed: {r.status_code} {r.text[:500]}")

#     # Some tenants return 201 with body containing id
#     if r.status_code == 201:
#         try:
#             return r.json()["id"]
#         except Exception:
#             pass

#     # Otherwise 202 with operation URL; poll it and fetch resulting resource
#     op = r.headers.get("Location") or r.headers.get("operation-location")
#     if not op:
#         raise RuntimeError("No operation location returned; cannot resolve team id.")

#     tok = _get_token()
#     status = {}
#     for _ in range(60):  # up to ~120s
#         pr = requests.get(op, headers=_headers(tok), timeout=60)
#         if pr.status_code == 200:
#             status = pr.json()
#             if status.get("status") in ("succeeded", "failed"):
#                 break
#         time.sleep(2)

#     res_loc = status.get("resourceLocation")
#     if res_loc:
#         gr = requests.get(res_loc, headers=_headers(tok), timeout=60)
#         if gr.status_code == 200:
#             return gr.json().get("id", "")
#     # Fallback: look up by display name
#     qr = requests.get(
#         f"{GRAPH}/groups?$filter=resourceProvisioningOptions/Any(x:x eq 'Team') and displayName eq '{display_name}'",
#         headers=_headers(tok),
#         timeout=60,
#     )
#     if qr.status_code == 200 and qr.json().get("value"):
#         return qr.json()["value"][0]["id"]
#     raise RuntimeError("Could not determine created team id. Check portal.")


# def list_channels(team_id: str) -> List[Dict]:
#     tok = _get_token()
#     r = requests.get(
#         f"{GRAPH}/teams/{team_id}/channels", headers=_headers(tok), timeout=60
#     )
#     if r.status_code != 200:
#         raise RuntimeError(f"List channels failed: {r.status_code} {r.text[:400]}")
#     return r.json().get("value", [])


# def create_channel_migration(
#     team_id: str,
#     display_name: str,
#     description: str = "",
#     membership_type: str = "standard",
#     created_iso: Optional[str] = None,
#     dry_run=False,
# ) -> str:
#     """
#     Create channel in migration mode. membership_type: 'standard' | 'private' | 'shared'
#     Returns channelId.
#     """
#     payload = {
#         "@microsoft.graph.channelCreationMode": "migration",
#         "displayName": display_name,
#         "description": description,
#         "membershipType": membership_type,  # Teams uses membershipType to distinguish channel kinds
#     }
#     if created_iso:
#         payload["createdDateTime"] = created_iso

#     if dry_run:
#         print(
#             f"DRY-RUN create channel {membership_type}: ",
#             json.dumps(payload, ensure_ascii=False)[:500],
#         )
#         return f"DRY_RUN_CH_{display_name}"

#     tok = _get_token()
#     r = requests.post(
#         f"{GRAPH}/teams/{team_id}/channels",
#         headers=_headers(tok),
#         data=json.dumps(payload),
#         timeout=120,
#     )
#     if r.status_code not in (201, 202):
#         raise RuntimeError(f"Create channel failed: {r.status_code} {r.text[:500]}")
#     if r.status_code == 201:
#         return r.json().get("id")

#     # Poll for visibility if 202 (rare)
#     for _ in range(30):
#         for ch in list_channels(team_id):
#             if ch.get("displayName") == display_name:
#                 return ch.get("id")
#         time.sleep(2)
#     raise RuntimeError("Channel did not appear after creation.")


# # -------- Message import --------
# def slack_ts_to_iso(ts: str) -> str:
#     # Slack ts like "1698269270.123456"
#     try:
#         sec = int((ts or "0").split(".")[0])
#         return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(sec))
#     except Exception:
#         return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# def iter_jsonl(path: Path) -> Iterable[Dict]:
#     with Path(path).open("r", encoding="utf-8") as f:
#         for line in f:
#             line = line.strip()
#             if line:
#                 yield json.loads(line)


# def import_message(
#     team_id: str,
#     channel_id: str,
#     *,
#     body_html: str,
#     created_iso: str,
#     as_user_id: Optional[str] = None,
#     dry_run=False,
# ):
#     payload = {
#         "messageType": "message",
#         "createdDateTime": created_iso,
#         "body": {"contentType": "html", "content": body_html or ""},
#     }
#     # NOTE: user attribution (“from”) intentionally omitted for now (varies by tenant policy).

#     if dry_run:
#         print(
#             f"DRY-RUN import → channel {channel_id}: ",
#             json.dumps(payload, ensure_ascii=False)[:300],
#         )
#         return

#     tok = _get_token()
#     # Use the migration endpoint on beta to surface the accurate errors (405/409/etc).
#     url = f"{GRAPH_BETA}/teams/{team_id}/channels/{channel_id}/messages/import"

#     r = requests.post(url, headers=_headers(tok), data=json.dumps(payload), timeout=60)

#     # Single error branch with verbose diagnostics
#     if r.status_code not in (201, 202):
#         try:
#             detail = r.text
#         except Exception:
#             detail = "<no-text>"
#         try:
#             hdrs = "\n".join([f"{k}: {v}" for k, v in r.headers.items()])
#         except Exception:
#             hdrs = "<no-headers>"
#         raise RuntimeError(
#             f"Import message failed: {r.status_code}\n"
#             f"URL: {url}\n"
#             f"HEADERS:\n{hdrs}\n"
#             f"BODY:\n{detail}\n"
#             f"PAYLOAD SENT:\n{json.dumps(payload, ensure_ascii=False)}"
#         )


# def complete_channel_migration(team_id: str, channel_id: str, dry_run=False):
#     if dry_run:
#         print(f"DRY-RUN complete channel migration: {channel_id}")
#         return
#     tok = _get_token()
#     r = requests.post(
#         # f"{GRAPH}/teams/{team_id}/channels/{channel_id}/completeMigration",
#         f"{GRAPH_BETA}/teams/{team_id}/channels/{channel_id}/completeMigration",
#         headers=_headers(tok),
#         timeout=60,
#     )
#     if r.status_code not in (200, 202, 204):
#         raise RuntimeError(
#             f"Complete channel migration failed: {r.status_code} {r.text[:400]}"
#         )


# def complete_team_migration(team_id: str, dry_run=False):
#     if dry_run:
#         print(f"DRY-RUN complete team migration: {team_id}")
#         return
#     tok = _get_token()
#     r = requests.post(
#         # f"{GRAPH}/teams/{team_id}/completeMigration"
#         f"{GRAPH_BETA}/teams/{team_id}/completeMigration", headers=_headers(tok), timeout=60
#     )
#     if r.status_code not in (200, 202, 204):
#         raise RuntimeError(
#             f"Complete team migration failed: {r.status_code} {r.text[:400]}"
#         )


# # -------- Load using a multi-team mapping --------
# def load_with_mapping(
#     mapping_path: Path,
#     messages_path: Path,
#     *,
#     rps: float = 4.0,
#     dry_run: bool = True,
#     complete_when_done: bool = False,
# ):
#     """
#     mapping.json structure:
#     {
#       "teams": {
#         "Team A": [
#           {"slack":"general","channel":"General","type":"standard","archive":false,"share_with":["partner.com"]},
#           {"slack":"private-x","channel":"Secret","type":"private"}
#         ],
#         "Team B": [ ... ]
#       }
#     }
#     """
#     mapping = json.loads(Path(mapping_path).read_text(encoding="utf-8"))
#     teams: Dict[str, List[Dict]] = mapping.get("teams", {})
    
#     # Helper: build reverse index slack_channel -> (team, channel_display, type)
#     reverse: Dict[str, Dict] = {}
#     for team_name, rows in teams.items():
#         for row in rows:
#             reverse[row["slack"]] = {
#                 "team": team_name,
#                 "channel": row["channel"],
#                 "type": row.get("type", "standard"),
#                 "archive": bool(row.get("archive", False)),
#                 "share_with": row.get("share_with", []),
#             }

#     # Create/reuse teams & channels
#     team_id_cache: Dict[str, str] = {}
#     channel_id_cache: Dict[tuple, str] = {}  # (team_id, channel_display) -> id

#     # Pre-scan messages to group them by (team, channel)
#     buckets: Dict[tuple, List[Dict]] = {}
#     for rec in iter_jsonl(messages_path):
#         slack_ch = rec.get("channel")
#         if slack_ch not in reverse:
#             # skip unmapped channels
#             continue
#         info = reverse[slack_ch]
#         key = (info["team"], info["channel"], info["type"])
#         buckets.setdefault(key, []).append(rec)

#     # Process each (team/channel) bucket
#     min_interval = 1.0 / max(rps, 0.1)

#     for (team_name, channel_display, ch_type), msgs in buckets.items():
#         # Ensure team exists (migration mode)
#         if team_name not in team_id_cache:
#             team_id_cache[team_name] = create_team_migration(team_name, dry_run=dry_run)
#         team_id = team_id_cache[team_name]

#         # Ensure channel exists
#         chan_key = (team_id, channel_display)
#         if chan_key not in channel_id_cache:
#             if dry_run:
#                 existing = {}
#             else:
#                 existing = {c.get("displayName"): c.get("id") for c in list_channels(team_id)}

#             if channel_display in existing:
#                 channel_id_cache[chan_key] = existing[channel_display]
#             else:
#                 channel_id_cache[chan_key] = create_channel_migration(
#                     team_id, channel_display, membership_type=ch_type, dry_run=dry_run
#                 )
#         channel_id = channel_id_cache[chan_key]

#         print(
#             f"== Importing {len(msgs)} messages into Team '{team_name}' → #{channel_display} ({ch_type}) =="
#         )

#         last = 0.0
#         for i, rec in enumerate(msgs, 1):
#             body_html = rec.get("text_html") or rec.get("text_raw") or ""
#             created_iso = slack_ts_to_iso(rec.get("ts") or "")
#             import_message(
#                 team_id,
#                 channel_id,
#                 body_html=body_html,
#                 created_iso=created_iso,
#                 dry_run=dry_run,
#             )

#             # Simple per-channel throttling
#             now = time.time()
#             delta = now - last
#             if delta < min_interval:
#                 time.sleep(min_interval - delta)
#             last = time.time()

#         if complete_when_done:
#             print(f"-- Completing channel migration: {channel_display}")
#             complete_channel_migration(team_id, channel_id, dry_run=dry_run)

#     if complete_when_done:
#         for team_name, team_id in team_id_cache.items():
#             print(f"-- Completing team migration: {team_name}")
#             complete_team_migration(team_id, dry_run=dry_run)
# # ---- BEGIN CHATGPT PATCH ----
# # Replaces create_team_migration with a safer version:
# # - Reuse existing Team (group with RPO:['Team']) by displayName
# # - Always include createdDateTime for migration teams (from env SLACK2TEAMS_CREATED_ISO or sane default)

# def create_team_migration(display_name: str, description: str = "", created_iso: str | None = None, dry_run: bool = False) -> str:
#     import os, json, requests
#     # Reuse token/header helpers and GRAPH/API constants from this module
#     tok = _acquire_token()
#     headers = _headers(tok)

#     # 0) If a Team already exists with this exact displayName, reuse it
#     def _odata_escape(s: str) -> str:
#         return s.replace("'", "''")

#     url = f"{API}/groups?$filter=displayName eq '{_odata_escape(display_name)}'&$select=id,displayName,resourceProvisioningOptions"
#     r = requests.get(url, headers=headers, timeout=60)
#     r.raise_for_status()
#     for g in r.json().get("value", []):
#         rpo = [x.lower() for x in g.get("resourceProvisioningOptions", [])]
#         if "team" in rpo:
#             return g["id"]  # Team already provisioned

#     # 1) If a Unified group exists (but not teamified), reuse its id and rely on team creation to teamify
#     url2 = f"{API}/groups?$filter=displayName eq '{_odata_escape(display_name)}'&$select=id,displayName,groupTypes,resourceProvisioningOptions"
#     r2 = requests.get(url2, headers=headers, timeout=60)
#     r2.raise_for_status()
#     existing_gid = None
#     for g in r2.json().get("value", []):
#         rpo = [x.lower() for x in g.get("resourceProvisioningOptions", [])]
#         if "team" not in rpo:
#             existing_gid = g["id"]
#             break

#     # 2) Ensure we have a createdDateTime (required in migration mode)
#     created_iso = created_iso or os.getenv("SLACK2TEAMS_CREATED_ISO") or "2024-01-02T12:00:00Z"

#     # 3) Create the Team in migration mode (with createdDateTime)
#     payload = {
#         "@microsoft.graph.teamCreationMode": "migration",
#         "template@odata.bind": f"{API}/teamsTemplates('standard')",
#         "displayName": display_name,
#         "description": description or "",
#         "createdDateTime": created_iso,
#     }

#     if dry_run:
#         return existing_gid or "DRYRUN-NO-ID"

#     # When a backing group already exists, we can PUT to /teams/{group-id}
#     if existing_gid:
#         put_url = f"{API}/teams/{existing_gid}"
#         r3 = requests.put(put_url, headers=headers, data=json.dumps(payload), timeout=120)
#         if r3.status_code not in (201, 202):
#             raise RuntimeError(f"Teamify existing group failed: {r3.status_code} {r3.text[:500]}")
#         # Resolve id by reading the group we just teamified
#         return existing_gid

#     # Otherwise POST /teams and then resolve id by name
#     r4 = requests.post(f"{API}/teams", headers=headers, data=json.dumps(payload), timeout=120)
#     if r4.status_code not in (201, 202):
#         raise RuntimeError(f"Create team failed: {r4.status_code} {r4.text[:500]}")

#     # Resolve the id by displayName (Graph returns 202 without body)
#     r5 = requests.get(f"{API}/groups?$filter=displayName eq '{_odata_escape(display_name)}'&$select=id", headers=headers, timeout=60)
#     r5.raise_for_status()
#     vals = r5.json().get("value", [])
#     if not vals:
#         # Final fallback: list last 20 teamified groups and try to match newest by name
#         r6 = requests.get(f"{API}/groups?$filter=resourceProvisioningOptions/any(x:x eq 'Team')&$select=id,displayName&$orderby=createdDateTime desc&$top=20",
#                           headers=headers, timeout=60)
#         r6.raise_for_status()
#         for g in r6.json().get("value", []):
#             if g.get("displayName") == display_name:
#                 return g["id"]
#         raise RuntimeError(f"Team created but id lookup by name failed for {display_name!r}")
#     return vals[0]["id"]

# # Override any earlier definition
# # noinspection PyRedeclaration
# create_team_migration = create_team_migration
# # ---- END CHATGPT PATCH ----
# # --- injected helpers: token + headers ---
# def _acquire_token():
#     import os
#     from msal import ConfidentialClientApplication
#     tenant = os.getenv("TENANT_ID")
#     client_id = os.getenv("CLIENT_ID")
#     client_secret = os.getenv("CLIENT_SECRET")
#     if not tenant or not client_id or not client_secret:
#         raise RuntimeError("Missing TENANT_ID/CLIENT_ID/CLIENT_SECRET in environment.")
#     app = ConfidentialClientApplication(
#         client_id,
#         authority=f"https://login.microsoftonline.com/{tenant}",
#         client_credential=client_secret,
#     )
#     tok = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
#     if "access_token" not in tok:
#         raise RuntimeError(f"Token failure: {tok}")
#     return tok

# def _headers(tok):
#     return {"Authorization": f"Bearer {tok['access_token']}", "Content-Type": "application/json"}
# def _get_token():
#     import os
#     from msal import ConfidentialClientApplication
#     GRAPH = "https://graph.microsoft.com"
#     tenant = os.getenv("TENANT_ID")
#     client_id = os.getenv("CLIENT_ID")
#     client_secret = os.getenv("CLIENT_SECRET")
#     app = ConfidentialClientApplication(
#         client_id,
#         authority=f"https://login.microsoftonline.com/{tenant}",
#         client_credential=client_secret,
#     )
#     tok = app.acquire_token_for_client(scopes=[f"{GRAPH}/.default"])
#     if "access_token" not in tok:
#         raise RuntimeError(f"Token failure: {tok}")
#     return tok

from __future__ import annotations

import os
import json
import time
from pathlib import Path
from typing import Dict, Iterable, Optional, List

import requests
from msal import ConfidentialClientApplication

# ------------ Graph base URLs ------------
GRAPH = "https://graph.microsoft.com"
API   = f"{GRAPH}/v1.0"
GRAPH_BETA = f"{GRAPH}/beta"

# ------------ Created date default ------------
def _default_created_iso():
    # Allow override via env (e.g., TEAM_CREATED_ISO=2024-01-02T12:00:00Z)
    return os.getenv("TEAM_CREATED_ISO") or "2024-01-02T12:00:00Z"


# ========== Auth helpers ==========
def _acquire_token() -> Dict[str, str]:
    tenant = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    if not tenant or not client_id or not client_secret:
        raise RuntimeError("Missing TENANT_ID/CLIENT_ID/CLIENT_SECRET in environment.")
    app = ConfidentialClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant}",
        client_credential=client_secret,
    )
    tok = app.acquire_token_for_client(scopes=[f"{GRAPH}/.default"])
    if "access_token" not in tok:
        raise RuntimeError(f"Token failure: {tok}")
    return tok

def _headers(tok: Dict[str, str]) -> Dict[str, str]:
    return {"Authorization": f"Bearer {tok['access_token']}", "Content-Type": "application/json"}


# ========== Team / Channel creation (migration mode) ==========
def create_team_migration(
    display_name: str,
    description: str = "",
    created_iso: Optional[str] = None,
    dry_run: bool = False,
) -> str:
    """
    Create or reuse a Team in migration mode. Returns teamId.
    Uses v1.0 endpoints. Migration flags are honored in v1.0.
    """
    def _odata_escape(s: str) -> str:
        return s.replace("'", "''")

    tok = _acquire_token()
    hdr = _headers(tok)

    # 0) If a Team already exists with this exact displayName, reuse it
    q = f"{API}/groups?$filter=displayName eq '{_odata_escape(display_name)}'&$select=id,displayName,resourceProvisioningOptions"
    r = requests.get(q, headers=hdr, timeout=60)
    r.raise_for_status()
    for g in r.json().get("value", []):
        rpo = [x.lower() for x in g.get("resourceProvisioningOptions", [])]
        if "team" in rpo:
            return g["id"]

    # 1) If a Unified group exists (but not teamified), remember its id
    r2 = requests.get(q, headers=hdr, timeout=60)
    r2.raise_for_status()
    existing_gid = None
    for g in r2.json().get("value", []):
        rpo = [x.lower() for x in g.get("resourceProvisioningOptions", [])]
        if "team" not in rpo:
            existing_gid = g["id"]
            break

    # created_iso = created_iso or os.getenv("SLACK2TEAMS_CREATED_ISO") or _default_created_iso()
    created_iso = created_iso or os.getenv("TEAM_CREATED_ISO") or "2022-01-01T00:00:00Z"

    payload = {
        "@microsoft.graph.teamCreationMode": "migration",
        "template@odata.bind": f"{API}/teamsTemplates('standard')",
        "displayName": display_name,
        "description": description or "",
        "createdDateTime": created_iso,
    }

    if dry_run:
        print("DRY-RUN create team payload:", json.dumps(payload, ensure_ascii=False)[:500])
        return f"DRY_RUN_TEAM_{display_name}"

    if existing_gid:
        # Teamify existing group
        put_url = f"{API}/teams/{existing_gid}"
        r3 = requests.put(put_url, headers=hdr, data=json.dumps(payload), timeout=120)
        if r3.status_code not in (201, 202):
            raise RuntimeError(f"Teamify existing group failed: {r3.status_code} {r3.text[:500]}")
        return existing_gid

    # Fresh Team
    r4 = requests.post(f"{API}/teams", headers=hdr, data=json.dumps(payload), timeout=120)
    if r4.status_code == 201:
        try:
            return r4.json()["id"]
        except Exception:
            pass
    if r4.status_code not in (201, 202):
        raise RuntimeError(f"Create team failed: {r4.status_code} {r4.text[:500]}")

    # Resolve id by displayName
    r5 = requests.get(
        f"{API}/groups?$filter=displayName eq '{_odata_escape(display_name)}'&$select=id",
        headers=hdr,
        timeout=60,
    )
    r5.raise_for_status()
    vals = r5.json().get("value", [])
    if vals:
        return vals[0]["id"]

    # Fallback: last 20 teams
    r6 = requests.get(
        f"{API}/groups?$filter=resourceProvisioningOptions/any(x:x eq 'Team')"
        f"&$select=id,displayName&$orderby=createdDateTime desc&$top=20",
        headers=hdr, timeout=60
    )
    r6.raise_for_status()
    for g in r6.json().get("value", []):
        if g.get("displayName") == display_name:
            return g["id"]
    raise RuntimeError(f"Team created but id lookup by name failed for {display_name!r}")


def list_channels(team_id: str) -> List[Dict]:
    tok = _acquire_token()
    r = requests.get(f"{API}/teams/{team_id}/channels", headers=_headers(tok), timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"List channels failed: {r.status_code} {r.text[:400]}")
    return r.json().get("value", [])


def create_channel_migration(
    team_id: str,
    display_name: str,
    description: str = "",
    membership_type: str = "standard",
    created_iso: Optional[str] = None,
    dry_run: bool = False,
) -> str:
    """
    Create channel in migration mode. membership_type: 'standard' | 'private' | 'shared'
    Returns channelId.
    """
    
    created_iso = created_iso or os.getenv("CHANNEL_CREATED_ISO") or "2022-01-01T00:00:00Z"

    payload = {
        "@microsoft.graph.channelCreationMode": "migration",
        "displayName": display_name,
        "description": description,
        "membershipType": membership_type,
    }
    if created_iso:
        payload["createdDateTime"] = created_iso

    if dry_run:
        print(f"DRY-RUN create channel {membership_type}: ", json.dumps(payload, ensure_ascii=False)[:500])
        return f"DRY_RUN_CH_{display_name}"

    tok = _acquire_token()
    r = requests.post(
        f"{API}/teams/{team_id}/channels",
        headers=_headers(tok),
        data=json.dumps(payload),
        timeout=120,
    )
    if r.status_code not in (201, 202):
        raise RuntimeError(f"Create channel failed: {r.status_code} {r.text[:500]}")
    if r.status_code == 201:
        return r.json().get("id")

    # Poll for visibility if 202
    for _ in range(30):
        for ch in list_channels(team_id):
            if ch.get("displayName") == display_name:
                return ch.get("id")
        time.sleep(2)
    raise RuntimeError("Channel did not appear after creation.")


# ========== Message import ==========
def slack_ts_to_iso(ts: str) -> str:
    # Slack ts like "1698269270.123456"
    try:
        sec = int((ts or "0").split(".")[0])
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(sec))
    except Exception:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def iter_jsonl(path: Path) -> Iterable[Dict]:
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


# def import_message(
#     team_id: str,
#     channel_id: str,
#     *,
#     body_html: str,
#     created_iso: str,
#     as_user_id: Optional[str] = None,
#     dry_run: bool = False,
# ):
#     """
#     Import a backdated message via the Teams Import API.
#     This endpoint is currently on /beta and requires the channel/team to be in migration mode
#     and not yet completed.
#     """
#     payload = {
#         "messageType": "message",
#         "createdDateTime": created_iso,
#         "body": {"contentType": "html", "content": body_html or ""},
#         # Optional: "from": {...}  # Omitted; attribution varies by tenant policy
#     }

#     if dry_run:
#         print(f"DRY-RUN import → channel {channel_id}: ", json.dumps(payload, ensure_ascii=False)[:300])
#         return

#     tok = _acquire_token()
#     url = f"{GRAPH_BETA}/teams/{team_id}/channels/{channel_id}/messages/import"
#     r = requests.post(url, headers=_headers(tok), data=json.dumps(payload), timeout=60)

#     if r.status_code not in (201, 202):
#         # Verbose diagnostics to help when Graph returns 405/409, etc.
#         try:
#             detail = r.text
#         except Exception:
#             detail = "<no-text>"
#         try:
#             hdrs = "\n".join([f"{k}: {v}" for k, v in r.headers.items()])
#         except Exception:
#             hdrs = "<no-headers>"
#         raise RuntimeError(
#             f"Import message failed: {r.status_code}\n"
#             f"URL: {url}\n"
#             f"HEADERS:\n{hdrs}\n"
#             f"BODY:\n{detail}\n"
#             f"PAYLOAD SENT:\n{json.dumps(payload, ensure_ascii=False)}"
#         )


# def complete_channel_migration(team_id: str, channel_id: str, dry_run: bool = False):
#     """
#     Mark a channel's migration complete (beta-only endpoint).
#     """
#     if dry_run:
#         print(f"DRY-RUN complete channel migration: {channel_id}")
#         return
#     tok = _acquire_token()
#     r = requests.post(
#         f"{GRAPH_BETA}/teams/{team_id}/channels/{channel_id}/completeMigration",
#         headers=_headers(tok),
#         timeout=60,
#     )
#     if r.status_code not in (200, 202, 204):
#         raise RuntimeError(f"Complete channel migration failed: {r.status_code} {r.text[:400]}")


# def complete_team_migration(team_id: str, dry_run: bool = False):
#     """
#     Mark a team's migration complete (beta-only endpoint).
#     """
#     if dry_run:
#         print(f"DRY-RUN complete team migration: {team_id}")
#         return
#     tok = _acquire_token()
#     r = requests.post(
#         f"{GRAPH_BETA}/teams/{team_id}/completeMigration",
#         headers=_headers(tok),
#         timeout=60,
#     )
#     if r.status_code not in (200, 202, 204):
#         raise RuntimeError(f"Complete team migration failed: {r.status_code} {r.text[:400]}")

# def import_message(
#     team_id: str,
#     channel_id: str,
#     *,
#     body_html: str,
#     created_iso: str,
#     as_user_id: Optional[str] = None,
#     dry_run: bool = False,
# ):
#     payload = {
#         "messageType": "message",
#         "createdDateTime": created_iso,
#         "body": {"contentType": "html", "content": body_html or ""},
#     }

#     if dry_run:
#         print(f"DRY-RUN import → channel {channel_id}: ", json.dumps(payload, ensure_ascii=False)[:300])
#         return

#     tok = _acquire_token()
#     # Correct endpoint for import flow (step 3): v1.0 messages collection
#     url = f"{API}/teams/{team_id}/channels/{channel_id}/messages"
#     r = requests.post(url, headers=_headers(tok), data=json.dumps(payload), timeout=60)

#     if r.status_code not in (200, 201, 202):
#         try:
#             detail = r.text
#         except Exception:
#             detail = "<no-text>"
#         try:
#             hdrs = "\n".join([f"{k}: {v}" for k, v in r.headers.items()])
#         except Exception:
#             hdrs = "<no-headers>"
#         raise RuntimeError(
#             f"Import message failed: {r.status_code}\n"
#             f"URL: {url}\n"
#             f"HEADERS:\n{hdrs}\n"
#             f"BODY:\n{detail}\n"
#             f"PAYLOAD SENT:\n{json.dumps(payload, ensure_ascii=False)}"
        # )
        
def import_message(
    team_id: str,
    channel_id: str,
    *,
    body_html: str,
    created_iso: str,
    as_user_id: Optional[str] = None,  # AAD objectId of the “attributed” user (optional)
    dry_run=False,
):
    # Fallback to a single “Migration Bot” user if no per-message user is mapped.
    # Set via env: IMPORT_FROM_USER_ID and IMPORT_FROM_DISPLAY_NAME (optional)
    env_user = os.getenv("IMPORT_FROM_USER_ID")
    env_name = os.getenv("IMPORT_FROM_DISPLAY_NAME") or "Slack Migration"

    from_block = None
    if as_user_id:
        from_block = {"user": {"id": as_user_id, "userIdentityType": "aadUser"}}
    elif env_user:
        from_block = {"user": {"id": env_user, "displayName": env_name, "userIdentityType": "aadUser"}}

    payload = {
        "createdDateTime": created_iso,
        "body": {"contentType": "html", "content": body_html or ""},
    }
    if from_block:
        payload["from"] = from_block

    if dry_run:
        print(f"DRY-RUN import → channel {channel_id}: ", json.dumps(payload, ensure_ascii=False)[:500])
        return

    tok = _acquire_token()
    # GA import path is v1.0 *without* /import
    url = f"{API}/teams/{team_id}/channels/{channel_id}/messages"
    r = requests.post(url, headers=_headers(tok), data=json.dumps(payload), timeout=60)
    
    print(r.status_code)

    if r.status_code not in (200, 201, 202):
        try:
            hdrs = "\n".join(f"{k}: {v}" for k, v in r.headers.items())
        except Exception:
            hdrs = "<no-headers>"
        raise RuntimeError(
            f"Import message failed: {r.status_code}\n"
            f"URL:\n{url}\nHEADERS:\n{hdrs}\nBODY:\n{r.text[:800]}\n"
            f"PAYLOAD SENT:\n{json.dumps(payload, ensure_ascii=False)}"
        )
        

def complete_channel_migration(team_id: str, channel_id: str, dry_run: bool = False):
    if dry_run:
        print(f"DRY-RUN complete channel migration: {channel_id}")
        return
    tok = _acquire_token()
    url = f"{API}/teams/{team_id}/channels/{channel_id}/completeMigration"
    r = requests.post(url, headers=_headers(tok), timeout=60)
    if r.status_code not in (200, 202, 204):
        raise RuntimeError(f"Complete channel migration failed: {r.status_code} {r.text[:400]}")

def complete_team_migration(team_id: str, dry_run: bool = False):
    if dry_run:
        print(f"DRY-RUN complete team migration: {team_id}")
        return
    tok = _acquire_token()
    url = f"{API}/teams/{team_id}/completeMigration"
    r = requests.post(url, headers=_headers(tok), timeout=60)
    if r.status_code not in (200, 202, 204):
        raise RuntimeError(f"Complete team migration failed: {r.status_code} {r.text[:400]}")



# ========== Load using a multi-team mapping ==========
def load_with_mapping(
    mapping_path: Path,
    messages_path: Path,
    *,
    rps: float = 4.0,
    dry_run: bool = True,
    complete_when_done: bool = False,
):
    """
    mapping.json structure:
    {
      "teams": {
        "Team A": [
          {"slack":"general","channel":"General","type":"standard","archive":false,"share_with":["partner.com"]},
          {"slack":"private-x","channel":"Secret","type":"private"}
        ],
        "Team B": [ ... ]
      }
    }
    """
    mapping = json.loads(Path(mapping_path).read_text(encoding="utf-8"))
    teams: Dict[str, List[Dict]] = mapping.get("teams", {})

    # Helper: build reverse index slack_channel -> (team, channel_display, type)
    reverse: Dict[str, Dict] = {}
    for team_name, rows in teams.items():
        for row in rows:
            reverse[row["slack"]] = {
                "team": team_name,
                "channel": row["channel"],
                "type": row.get("type", "standard"),
                "archive": bool(row.get("archive", False)),
                "share_with": row.get("share_with", []),
            }

    # Create/reuse teams & channels
    team_id_cache: Dict[str, str] = {}
    channel_id_cache: Dict[tuple, str] = {}  # (team_id, channel_display) -> id

    # Pre-scan messages to group them by (team, channel)
    buckets: Dict[tuple, List[Dict]] = {}
    for rec in iter_jsonl(messages_path):
        slack_ch = rec.get("channel")
        if slack_ch not in reverse:
            # skip unmapped channels
            continue
        info = reverse[slack_ch]
        key = (info["team"], info["channel"], info["type"])
        buckets.setdefault(key, []).append(rec)

    # Process each (team/channel) bucket
    min_interval = 1.0 / max(rps, 0.1)

    for (team_name, channel_display, ch_type), msgs in buckets.items():
        # Ensure team exists (migration mode)
        if team_name not in team_id_cache:
            team_id_cache[team_name] = create_team_migration(team_name, dry_run=dry_run)
        team_id = team_id_cache[team_name]

        # Ensure channel exists
        chan_key = (team_id, channel_display)
        if chan_key not in channel_id_cache:
            existing = {} if dry_run else {c.get("displayName"): c.get("id") for c in list_channels(team_id)}
            if channel_display in existing:
                channel_id_cache[chan_key] = existing[channel_display]
            else:
                channel_id_cache[chan_key] = create_channel_migration(
                    team_id, channel_display, membership_type=ch_type, dry_run=dry_run
                )
        channel_id = channel_id_cache[chan_key]

        print(f"== Importing {len(msgs)} messages into Team '{team_name}' → #{channel_display} ({ch_type}) ==")

        last = 0.0
        for i, rec in enumerate(msgs, 1):
            body_html = rec.get("text_html") or rec.get("text_raw") or ""
            created_iso = slack_ts_to_iso(rec.get("ts") or "")
            import_message(
                team_id,
                channel_id,
                body_html=body_html,
                created_iso=created_iso,
                dry_run=dry_run,
            )

            # Simple per-channel throttling
            now = time.time()
            delta = now - last
            if delta < min_interval:
                time.sleep(min_interval - delta)
            last = time.time()

        if complete_when_done:
            print(f"-- Completing channel migration: {channel_display}")
            complete_channel_migration(team_id, channel_id, dry_run=dry_run)

    if complete_when_done:
        for team_name, team_id in team_id_cache.items():
            print(f"-- Completing team migration: {team_name}")
            complete_team_migration(team_id, dry_run=dry_run)
