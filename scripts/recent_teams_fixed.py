import os, requests, datetime
from msal import ConfidentialClientApplication

GRAPH="https://graph.microsoft.com"; API=f"{GRAPH}/v1.0"
app = ConfidentialClientApplication(
    os.getenv("CLIENT_ID"),
    authority=f"https://login.microsoftonline.com/{os.getenv('TENANT_ID')}",
    client_credential=os.getenv("CLIENT_SECRET")
)
tok = app.acquire_token_for_client(scopes=[f"{GRAPH}/.default"])
if "access_token" not in tok:
    raise SystemExit(f"Token failure: {tok}")

h={
  "Authorization": f"Bearer {tok['access_token']}",
  "ConsistencyLevel": "eventual"
}

# Get recent Unified groups (bigger window, sort client-side)
url = f"{API}/groups?$filter=groupTypes/any(x:x eq 'Unified')&$select=id,displayName,createdDateTime,resourceProvisioningOptions&$top=100"
r = requests.get(url, headers=h, timeout=60)
print("=>", r.status_code)
if r.status_code != 200:
    print(r.text); raise SystemExit()

groups = r.json().get("value", [])
# Keep only those that are Teams
teams = [g for g in groups if 'Team' in (g.get('resourceProvisioningOptions') or [])]
# Sort newest first locally
teams.sort(key=lambda g: g.get("createdDateTime") or "", reverse=True)

for g in teams[:25]:
    print(f"- {g.get('createdDateTime')}  id:{g['id']}  name:{g['displayName']}  RPO:{g.get('resourceProvisioningOptions',[])}")
