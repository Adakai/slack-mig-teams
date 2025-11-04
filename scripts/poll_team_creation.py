import os, sys, time, requests
from msal import ConfidentialClientApplication

GRAPH = "https://graph.microsoft.com/"
API   = f"{GRAPH}/v1.0"

if len(sys.argv) < 2:
    raise SystemExit("Usage: python poll_team_creation.py <TEAM_ID>")

team_id = sys.argv[1]

app = ConfidentialClientApplication(
    os.getenv("CLIENT_ID"),
    authority=f"https://login.microsoftonline.com/{os.getenv('TENANT_ID')}",
    client_credential=os.getenv("CLIENT_SECRET")
)
tok = app.acquire_token_for_client(scopes=[f"{GRAPH}/.default"])
if "access_token" not in tok:
    raise SystemExit(f"Token failure: {tok}")

h = {"Authorization": f"Bearer {tok['access_token']}"}

op_url   = f"/teams('{team_id}')/operations('00000000-0000-0000-0000-000000000000')"
team_url = f"/teams('{team_id}')"

# Poll operation
while True:
    r = requests.get(f"{GRAPH}{op_url}", headers=h, timeout=60)
    if r.status_code == 404:
        # Some tenants don’t expose the operation — break and try to GET team
        print("operation status: (not found, continuing)")
        break
    r.raise_for_status()
    s = r.json().get("status")
    print("operation status:", s)
    if s in ("succeeded","failed","cancelled"):
        if s != "succeeded":
            raise SystemExit(r.text)
        break
    time.sleep(5)

# Check team
r = requests.get(f"{GRAPH}{team_url}", headers=h, timeout=60)
print("team GET =>", r.status_code)
print((r.text or "")[:500])
