import os, sys, requests
from msal import ConfidentialClientApplication

GRAPH="https://graph.microsoft.com"; API=f"{GRAPH}/v1.0"

q = sys.argv[1] if len(sys.argv) > 1 else "Pilot"
print(f"Searching groups that start with: {q!r}")

app = ConfidentialClientApplication(
    os.getenv("CLIENT_ID"),
    authority=f"https://login.microsoftonline.com/{os.getenv('TENANT_ID')}",
    client_credential=os.getenv("CLIENT_SECRET")
)
tok = app.acquire_token_for_client(scopes=[f"{GRAPH}/.default"])
if "access_token" not in tok:
    raise SystemExit(f"Token failure: {tok}")
h = {"Authorization": f"Bearer {tok['access_token']}"}

# 1) Exact match
r = requests.get(f"{API}/groups?$filter=displayName eq '{q}'&$select=id,displayName,resourceProvisioningOptions", headers=h, timeout=60)
print("\nEXACT MATCH =>", r.status_code)
for g in r.json().get("value", []):
    print(f"- id:{g['id']}  name:{g['displayName']}  RPO:{g.get('resourceProvisioningOptions',[])}")

# 2) startswith (case-sensitive in Graph, so we try both the input and upper-cased)
for probe in {q, q.upper()}:
    r = requests.get(f"{API}/groups?$filter=startswith(displayName,'{probe}')&$select=id,displayName,resourceProvisioningOptions", headers=h, timeout=60)
    print(f"\nSTARTSWITH '{probe}' =>", r.status_code)
    for g in r.json().get("value", []):
        print(f"- id:{g['id']}  name:{g['displayName']}  RPO:{g.get('resourceProvisioningOptions',[])}")
