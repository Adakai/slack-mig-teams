"""Debug helper: import a single HTML message into a Teams channel via the migration import API.

Usage (PowerShell):
  $env:TEAM_ID = "<team-id>"
  $env:CHANNEL_ID = "<channel-id>"
  pipenv run python .\scripts\debug_import_one.py "Test message from debug script"

Or provide team & channel on the command line:
  pipenv run python .\scripts\debug_import_one.py <team_id> <channel_id> "Test message"

This prints status code, response headers and body to help debug failures.

Note: Requires TENANT_ID, CLIENT_ID, CLIENT_SECRET in env (app must have Teamwork.Migrate.All).
"""
import os
import sys
import time
import json
import requests
from msal import ConfidentialClientApplication

GRAPH = "https://graph.microsoft.com"
GRAPH_BETA = "https://graph.microsoft.com/beta"


def acquire_token():
    tenant = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    if not all([tenant, client_id, client_secret]):
        print("Missing TENANT_ID/CLIENT_ID/CLIENT_SECRET in environment.")
        sys.exit(2)
    app = ConfidentialClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant}",
        client_credential=client_secret,
    )
    tok = app.acquire_token_for_client(scopes=[f"{GRAPH}/.default"]) 
    if "access_token" not in tok:
        print("Token acquisition failed:", tok)
        sys.exit(3)
    return tok["access_token"]


def main():
    # Accept team/channel via env or args
    team_id = os.getenv("TEAM_ID")
    channel_id = os.getenv("CHANNEL_ID")
    args = [a for a in sys.argv[1:]]
    if len(args) >= 2:
        team_id = team_id or args[0]
        channel_id = channel_id or args[1]
        msg = " ".join(args[2:]) or "Debug import message"
    else:
        if len(args) == 1:
            msg = args[0]
        else:
            msg = "Debug import message"

    if not team_id or not channel_id:
        print("Usage: set TEAM_ID and CHANNEL_ID env vars, or pass them as the first two args.\nExample:\n  $env:TEAM_ID='...'; $env:CHANNEL_ID='...'; pipenv run python .\\scripts\\debug_import_one.py 'Hello'")
        sys.exit(1)

    created = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    body_html = f"<div>{msg}</div>"
    payload = {
        "messageType": "message",
        "createdDateTime": created,
        "body": {"contentType": "html", "content": body_html},
    }

    token = acquire_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{GRAPH_BETA}/teams/{team_id}/channels/{channel_id}/messages/import"

    print("POST", url)
    print("PAYLOAD:", json.dumps(payload, ensure_ascii=False))
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
    except Exception as e:
        print("Request failed:", e)
        sys.exit(4)

    print("STATUS:", r.status_code)
    print("HEADERS:")
    for k, v in r.headers.items():
        print(f"  {k}: {v}")
    print("BODY:")
    try:
        print(r.text)
    except Exception:
        print("<unable to print body>")

    # Exit code hint: non-2xx -> 10
    if r.status_code not in (200, 201, 202, 204):
        sys.exit(10)


if __name__ == '__main__':
    main()
