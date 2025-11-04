import os, requests
from msal import ConfidentialClientApplication

tenant = os.getenv("TENANT_ID")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

app = ConfidentialClientApplication(
    client_id, authority=f"https://login.microsoftonline.com/{tenant}",
    client_credential=client_secret
)
tok = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
if "access_token" not in tok:
    raise SystemExit(f"Token failure: {tok}")

headers = {
    "Authorization": f"Bearer {tok['access_token']}",
    "Content-Type": "application/json"
}

payload = {
    "template@odata.bind": "https://graph.microsoft.com/v1.0/teamsTemplates('standard')",
    "displayName": "PILOT – Jer-nee - MKTG",
    "description": "Slack import pilot",
    "visibility": "Private"
}

r = requests.post("https://graph.microsoft.com/v1.0/teams", json=payload, headers=headers)
print("POST /teams =>", r.status_code)
print(r.text)
