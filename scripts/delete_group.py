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

# Optional sanity check
g = requests.get(f"{API}/groups/{gid}?$select=id,displayName", headers=h, timeout=60)
print("GET /groups =>", g.status_code, g.text[:200])

# Delete
r = requests.delete(f"{API}/groups/{gid}", headers=h, timeout=60)
print("DELETE /groups =>", r.status_code or 204)
