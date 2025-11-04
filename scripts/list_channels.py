import os, sys, requests
from msal import ConfidentialClientApplication

GRAPH="https://graph.microsoft.com"; API=f"{GRAPH}/v1.0"
tid = sys.argv[1] if len(sys.argv)>1 else ""
if not tid: raise SystemExit("Usage: list_channels.py <TEAM_ID>")

app = ConfidentialClientApplication(
    os.getenv("CLIENT_ID"),
    authority=f"https://login.microsoftonline.com/{os.getenv('TENANT_ID')}",
    client_credential=os.getenv("CLIENT_SECRET"),
)
tok = app.acquire_token_for_client(scopes=[f"{GRAPH}/.default"])
if "access_token" not in tok: raise SystemExit(f"Token failure: {tok}")
h={"Authorization": f"Bearer {tok['access_token']}"}

r = requests.get(f"{API}/teams/{tid}/channels?$select=id,displayName", headers=h, timeout=60)
print("status:", r.status_code)
print(r.text)
