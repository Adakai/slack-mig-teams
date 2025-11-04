import os, requests
from msal import ConfidentialClientApplication

GRAPH="https://graph.microsoft.com"; API=f"{GRAPH}/v1.0"
team_id="7c88d639-24ba-4d98-8a69-fca61b87a7c2"
chan_id="19:0584d655d1ac498688567723c3a6d57f@thread.tacv2"

app=ConfidentialClientApplication(
    os.getenv("CLIENT_ID"),
    authority=f"https://login.microsoftonline.com/{os.getenv('TENANT_ID')}",
    client_credential=os.getenv("CLIENT_SECRET")
)
tok=app.acquire_token_for_client(scopes=[f"{GRAPH}/.default"])
if "access_token" not in tok:
    raise SystemExit(f"Token failure: {tok}")

h={"Authorization":f"Bearer {tok['access_token']}"}
r=requests.get(f"{API}/teams/{team_id}/channels/{chan_id}/messages?$top=5",headers=h,timeout=60)
print("status:",r.status_code)
print(r.text[:1500])
