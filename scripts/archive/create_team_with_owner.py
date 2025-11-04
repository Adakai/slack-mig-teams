import os, requests
from msal import ConfidentialClientApplication

GRAPH_ROOT = "https://graph.microsoft.com"
GRAPH_API  = f"{GRAPH_ROOT}/v1.0"

tenant = os.getenv("TENANT_ID")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
owner_upn = os.getenv("OWNER_UPN")
team_name = "PILOT – Jer-nee - MKTG"

if not owner_upn:
    raise SystemExit("Missing OWNER_UPN in .env")

app = ConfidentialClientApplication(
    client_id,
    authority=f"https://login.microsoftonline.com/{tenant}",
    client_credential=client_secret,
)

# ✅ Correct scope (no /v1.0 here)
tok = app.acquire_token_for_client(scopes=[f"{GRAPH_ROOT}/.default"])
if "access_token" not in tok:
    raise SystemExit(f"Token failure: {tok}")

h = {"Authorization": f"Bearer {tok['access_token']}", "Content-Type": "application/json"}

# 1) Resolve owner user id
r = requests.get(
    f"{GRAPH_API}/users?$filter=userPrincipalName eq '{owner_upn}'&$select=id,displayName,userPrincipalName",
    headers=h, timeout=60
)
r.raise_for_status()
vals = r.json().get("value", [])
if not vals:
    raise SystemExit(f"OWNER_UPN not found: {owner_upn}")
owner_id = vals[0]["id"]

# 2) Create migration-mode team with an owner
payload = {
    "@microsoft.graph.teamCreationMode": "migration",
    "template@odata.bind": f"{GRAPH_API}/teamsTemplates('standard')",
    "displayName": team_name,
    "description": "Slack import pilot",
    "visibility": "Private",
    "members": [
        {
            "@odata.type": "#microsoft.graph.aadUserConversationMember",
            "roles": ["owner"],
            "user@odata.bind": f"{GRAPH_API}/users('{owner_id}')"
        }
    ]
}

r2 = requests.post(f"{GRAPH_API}/teams", json=payload, headers=h, timeout=120)
print("POST /teams =>", r2.status_code)
print(r2.text or "")
