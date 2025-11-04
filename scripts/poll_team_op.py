import os, sys, time, requests
from msal import ConfidentialClientApplication
GRAPH="https://graph.microsoft.com"; API=f"{GRAPH}/v1.0"
op_url = sys.argv[1] if len(sys.argv)>1 else ""
team_url = sys.argv[2] if len(sys.argv)>2 else ""
if not op_url or not team_url: raise SystemExit("Usage: poll_team_op.py <operation-url> <team-url>")
app = ConfidentialClientApplication(os.getenv("CLIENT_ID"),
    authority=f"https://login.microsoftonline.com/{os.getenv('TENANT_ID')}",
    client_credential=os.getenv("CLIENT_SECRET"))
tok = app.acquire_token_for_client(scopes=[f"{GRAPH}/.default"])
if "access_token" not in tok: raise SystemExit(f"Token failure: {tok}")
h={"Authorization":f"Bearer {tok['access_token']}"}
while True:
    r=requests.get(f"{GRAPH}{op_url}",headers=h,timeout=60); r.raise_for_status()
    s=r.json().get("status"); print("operation status:",s)
    if s in ("succeeded","failed","cancelled"): break
    time.sleep(5)
if s!="succeeded": raise SystemExit(r.text)
r=requests.get(f"{GRAPH}{team_url}",headers=h,timeout=60); print("team GET =>",r.status_code); print(r.text[:400])
