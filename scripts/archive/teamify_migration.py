import os, sys, requests
from msal import ConfidentialClientApplication

GRAPH_ROOT = "https://graph.microsoft.com"
API        = f"{GRAPH_ROOT}/v1.0"

group_id = sys.argv[1] if len(sys.argv) > 1 else ""
if not group_id:
    raise SystemExit("Usage: python teamify_migration.py <GROUP_ID>")

tenant = os.getenv("TENANT_ID")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

app = ConfidentialClientApplication(
    client_id,
    authority=f"https://login.microsoftonline.com/{tenant}",
    client_credential=client_secret,
)
tok = app.acquire_token_for_client(scopes=[f"{GRAPH_ROOT}/.default"])
if "access_token" not in tok:
    raise SystemExit(f"Token failure: {tok}")

h = {"Authorization": f"Bearer {tok['access_token']}", "Content-Type": "application/json"}

payload = {
    "@microsoft.graph.teamCreationMode": "migration",
    "template@odata.bind": f"{API}/teamsTemplates('standard')",
    "group@odata.bind": f"{API}/groups('{group_id}')"
}

r = requests.post(f"{API}/teams", headers=h, json=payload, timeout=120)
print("POST /teams =>", r.status_code)
print(r.text or "")
