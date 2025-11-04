"""Inspect channel and team resources (v1.0 and beta) and print headers + body.

Usage (PowerShell):
  $env:TEAM_ID = "<team-id>"
  $env:CHANNEL_ID = "<channel-id>"
  pipenv run python .\scripts\inspect_channel.py

Or pass as args: pipenv run python .\scripts\inspect_channel.py <team_id> <channel_id>
"""
import os
import sys
import json
import requests
from msal import ConfidentialClientApplication

GRAPH = "https://graph.microsoft.com"

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

def pretty_headers(hdrs):
    return "\n".join([f"  {k}: {v}" for k, v in hdrs.items()])

def do_get(url, headers):
    print(f"GET {url}")
    try:
        r = requests.get(url, headers=headers, timeout=30)
    except Exception as e:
        print("Request failed:", repr(e))
        return None
    print("STATUS:", r.status_code)
    print("HEADERS:\n" + pretty_headers(r.headers))
    try:
        print("BODY:\n", r.text)
    except Exception:
        print("BODY: <unprintable>")
    return r

def main():
    team_id = os.getenv("TEAM_ID")
    channel_id = os.getenv("CHANNEL_ID")
    args = [a for a in sys.argv[1:]]
    if len(args) >= 2:
        team_id = team_id or args[0]
        channel_id = channel_id or args[1]

    if not team_id or not channel_id:
        print("Usage: set TEAM_ID and CHANNEL_ID env vars, or pass them as args")
        sys.exit(1)

    token = acquire_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Check team (groups) resource
    do_get(f"{GRAPH}/v1.0/groups/{team_id}?$select=id,displayName,resourceProvisioningOptions,groupTypes,createdDateTime", headers)

    # Check team resource
    do_get(f"{GRAPH}/v1.0/teams/{team_id}", headers)

    # Channel: v1.0
    do_get(f"{GRAPH}/v1.0/teams/{team_id}/channels/{channel_id}", headers)

    # Channel: beta
    do_get(f"{GRAPH}/beta/teams/{team_id}/channels/{channel_id}", headers)

if __name__ == '__main__':
    main()
