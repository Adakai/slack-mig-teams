import os, sys, requests, datetime
from msal import ConfidentialClientApplication
GRAPH="https://graph.microsoft.com"; API=f"{GRAPH}/v1.0"
team_id=sys.argv[1]; chan_name=sys.argv[2]; created="2024-01-02T12:00:00Z"
app=ConfidentialClientApplication(os.getenv("CLIENT_ID"),
  authority=f"https://login.microsoftonline.com/{os.getenv('TENANT_ID')}",
  client_credential=os.getenv("CLIENT_SECRET"))
tok=app.acquire_token_for_client(scopes=[f"{GRAPH}/.default"])
h={"Authorization":f"Bearer {tok['access_token']}", "Content-Type":"application/json"}
payload={"@microsoft.graph.channelCreationMode":"migration","displayName":chan_name,
         "membershipType":"standard","createdDateTime":created}
r=requests.post(f"{API}/teams/{team_id}/channels",headers=h,json=payload,timeout=120)
print(r.status_code); print(r.text)
