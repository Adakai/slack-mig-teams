import os, re, json, requests
from msal import ConfidentialClientApplication

GRAPH_ROOT = "https://graph.microsoft.com"
API        = f"{GRAPH_ROOT}/v1.0"

team_name = "PILOT – Jer-nee - MKTG"
owner_upn = os.getenv("OWNER_UPN")
if not owner_upn:
    raise SystemExit("Missing OWNER_UPN in .env")

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

# 0) Resolve owner id
u = requests.get(f"{API}/users?$filter=userPrincipalName eq '{owner_upn}'&$select=id,displayName",
                 headers=h, timeout=60)
u.raise_for_status()
vals = u.json().get("value", [])
if not vals:
    raise SystemExit(f"OWNER_UPN not found: {owner_upn}")
owner_id = vals[0]["id"]

# 1) Make a unique mailNickname
base = re.sub(r"[^a-z0-9]", "", team_name.lower())
if not base:
    base = "team"
nick = base[:50]
# ensure unique
def exists(n):
    r = requests.get(f"{API}/groups?$filter=mailNickname eq '{n}'&$select=id", headers=h, timeout=60)
    r.raise_for_status()
    return len(r.json().get("value", [])) > 0

suffix = 0
unique = nick
while exists(unique):
    suffix += 1
    unique = f"{nick[:45]}{suffix}"

payload = {
    "displayName": team_name,
    "description": "Slack import pilot",
    "groupTypes": ["Unified"],
    "mailEnabled": True,
    "mailNickname": unique,
    "securityEnabled": False,
    "visibility": "Private",
    # set owner
    "owners@odata.bind": [f"{API}/users('{owner_id}')"]
}

r = requests.post(f"{API}/groups", headers=h, json=payload, timeout=120)
print("POST /groups =>", r.status_code)
print(r.text or "")
if r.status_code not in (201, 202):
    raise SystemExit("Group create failed.")

gid = r.json()["id"]
print("Created group id:", gid)
