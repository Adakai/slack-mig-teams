import os, requests, datetime
from msal import ConfidentialClientApplication

GRAPH = "https://graph.microsoft.com"
API   = f"{GRAPH}/v1.0"

team_name = "PILOT – Jer-nee - MKTG"
created   = "2024-01-02T12:00:00Z"  # must be in the past

app = ConfidentialClientApplication(
    os.getenv("CLIENT_ID"),
    authority=f"https://login.microsoftonline.com/{os.getenv('TENANT_ID')}",
    client_credential=os.getenv("CLIENT_SECRET"),
)
tok = app.acquire_token_for_client(scopes=[f"{GRAPH}/.default"])
assert "access_token" in tok, tok
h = {"Authorization": f"Bearer {tok['access_token']}", "Content-Type": "application/json"}

payload = {
  "@microsoft.graph.teamCreationMode": "migration",
  "template@odata.bind": f"{API}/teamsTemplates('standard')",
  "displayName": team_name,
  "description": "Slack import pilot",
  "createdDateTime": created
}

r = requests.post(f"{API}/teams", headers=h, json=payload, timeout=120)
print("POST /teams =>", r.status_code)
print("Location:", r.headers.get("Location", ""))
print("Content-Location:", r.headers.get("Content-Location", ""))
