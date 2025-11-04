import os, sys, requests
from msal import ConfidentialClientApplication

GRAPH = "https://graph.microsoft.com"; API = f"{GRAPH}/v1.0"
if len(sys.argv) < 2: raise SystemExit("Usage: get_team_state.py <GROUP_OR_TEAM_ID>")
tid = sys.argv[1]

app = ConfidentialClientApplication(
    os.getenv("CLIENT_ID"),
    authority=f"https://login.microsoftonline.com/{os.getenv('TENANT_ID')}",
    client_credential=os.getenv("CLIENT_SECRET"),
)
tok = app.acquire_token_for_client(scopes=[f"{GRAPH}/.default"])
if "access_token" not in tok: raise SystemExit(f"Token failure: {tok}")
h = {"Authorization": f"Bearer {tok['access_token']}"}

def get(url):
    r = requests.get(url, headers=h, timeout=60)
    return r.status_code, (r.json() if r.text else {})

# A) Does the underlying M365 Group exist?
sc, grp = get(f"{API}/groups/{tid}")
print("GET /groups/{id} =>", sc)

# B) Has the Team been provisioned on that group?
sc, team_on_group = get(f"{API}/groups/{tid}/team")
print("GET /groups/{id}/team =>", sc, ("(team exists)" if sc==200 else ""))

# C) Direct team read
sc, team = get(f"{API}/teams/{tid}")
print("GET /teams/{id} =>", sc)

# D) Any operations hanging around?
sc, ops = get(f"{API}/teams/{tid}/operations")
print("GET /teams/{id}/operations =>", sc)
if sc==200: 
    print("ops:", [o.get("id")+" "+o.get("status","") for o in ops.get("value", [])])
