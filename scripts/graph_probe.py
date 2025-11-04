import os, sys, requests
from msal import ConfidentialClientApplication

GRAPH = "https://graph.microsoft.com/v1.0"
target = sys.argv[1] if len(sys.argv) > 1 else ""

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

h = {"Authorization": f"Bearer {tok['access_token']}"}

def get_json(url):
    r = requests.get(url, headers=h, timeout=60)
    try:
        body = r.json() if r.text else {}
    except Exception:
        body = {"raw": r.text}
    return r.status_code, body

# Build queries
queries = []
if target:
    safe_target = target.replace("'", "''")
    queries.append(f"{GRAPH}/groups?$filter=displayName eq '{safe_target}'&$select=id,displayName,resourceProvisioningOptions")
queries.append(f"{GRAPH}/groups?$filter=startswith(displayName,'PILOT')&$select=id,displayName,resourceProvisioningOptions")

seen = {}
for url in queries:
    code, data = get_json(url)
    print(f"\nGET {url}\n=> {code}")
    for g in data.get("value", []):
        rid = g["id"]
        if rid in seen:
            continue
        seen[rid] = g
        rpo = g.get("resourceProvisioningOptions", [])
        print(f"- group: {g['displayName']}  id:{rid}  RPO:{rpo}")

# For each candidate, check Team status and channels
for rid, g in seen.items():
    print(f"\nChecking /teams/{rid} for '{g['displayName']}' …")
    code, data = get_json(f"{GRAPH}/teams/{rid}")
    print(f"=> /teams status: {code}")
    if code == 200:
        code2, chans = get_json(f"{GRAPH}/teams/{rid}/channels")
        count = len(chans.get('value', [])) if isinstance(chans, dict) else 0
        print(f"=> channels status: {code2}, count: {count}")
