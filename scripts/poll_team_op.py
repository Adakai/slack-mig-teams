import os, sys, time, requests
from msal import ConfidentialClientApplication

GRAPH = "https://graph.microsoft.com"
API = f"{GRAPH}/v1.0"

op_url = sys.argv[1] if len(sys.argv) > 1 else ""
team_url = sys.argv[2] if len(sys.argv) > 2 else ""
if not op_url or not team_url:
    raise SystemExit("Usage: poll_team_op.py <operation-url> <team-url>")

def _make_full_url(path_or_url: str) -> str:
    # Accept either a full URL or a relative path (/teams/...) or a bare path (teams/...).
    # For relative paths prefer the API root (/v1.0) so '/teams/..' => 'https://graph.microsoft.com/v1.0/teams/...'
    p = path_or_url.strip()
    if p.lower().startswith("http"):
        return p
    if p.startswith("/"):
        return f"{API}{p}"
    return f"{API}/{p}"

op_full = _make_full_url(op_url)
team_full = _make_full_url(team_url)
print("Requesting operation URL:", op_full)
print("Requesting team URL:", team_full)

app = ConfidentialClientApplication(
    os.getenv("CLIENT_ID"),
    authority=f"https://login.microsoftonline.com/{os.getenv('TENANT_ID')}",
    client_credential=os.getenv("CLIENT_SECRET"),
)
tok = app.acquire_token_for_client(scopes=[f"{GRAPH}/.default"])
if "access_token" not in tok:
    raise SystemExit(f"Token failure: {tok}")
h = {"Authorization": f"Bearer {tok['access_token']}"}

try:
    while True:
        r = requests.get(op_full, headers=h, timeout=60)
        r.raise_for_status()
        s = r.json().get("status")
        print("operation status:", s)
        if s in ("succeeded", "failed", "cancelled"):
            break
        time.sleep(5)
except requests.exceptions.RequestException as e:
    print("Error while polling operation URL:", repr(e))
    raise

if s != "succeeded":
    raise SystemExit(r.text)

try:
    r = requests.get(team_full, headers=h, timeout=60)
    print("team GET =>", r.status_code)
    print(r.text[:400])
except requests.exceptions.RequestException as e:
    print("Error while fetching team URL:", repr(e))
    raise
