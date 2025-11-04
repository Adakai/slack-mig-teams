import os, sys, requests
from msal import ConfidentialClientApplication

GRAPH="https://graph.microsoft.com"; API=f"{GRAPH}/v1.0"
raw = sys.argv[1] if len(sys.argv)>1 else "Pilot - Jer-nee - MKTG"

# Try common dash variants
variants = {raw}
variants.add(raw.replace(" - ", " – "))  # hyphen -> en-dash
variants.add(raw.replace(" – ", " - "))  # en-dash -> hyphen

app = ConfidentialClientApplication(
    os.getenv("CLIENT_ID"),
    authority=f"https://login.microsoftonline.com/{os.getenv('TENANT_ID')}",
    client_credential=os.getenv("CLIENT_SECRET")
)
tok = app.acquire_token_for_client(scopes=[f"{GRAPH}/.default"])
if "access_token" not in tok:
    raise SystemExit(f"Token failure: {tok}")
h={"Authorization":f"Bearer {tok['access_token']}"}

seen = False
for q in variants:
    r = requests.get(f"{API}/groups?$filter=displayName eq '{q}'&$select=id,displayName,resourceProvisioningOptions", headers=h, timeout=60)
    print(f"\nEXACT '{q}' =>", r.status_code)
    for g in r.json().get("value", []):
        seen = True
        print(f"- id:{g['id']}  name:{g['displayName']}  RPO:{g.get('resourceProvisioningOptions',[])}")

# If still nothing exact, fall back to startswith on the first word
prefix = raw.split()[0]
r = requests.get(f"{API}/groups?$filter=startswith(displayName,'{prefix}')&$select=id,displayName,resourceProvisioningOptions", headers=h, timeout=60)
print(f"\nSTARTSWITH '{prefix}' =>", r.status_code)
for g in r.json().get("value", []):
    print(f"- id:{g['id']}  name:{g['displayName']}  RPO:{g.get('resourceProvisioningOptions',[])}")
