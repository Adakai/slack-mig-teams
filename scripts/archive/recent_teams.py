import os, requests, datetime
from msal import ConfidentialClientApplication

GRAPH="https://graph.microsoft.com"; API=f"{GRAPH}/v1.0"
app = ConfidentialClientApplication(os.getenv("CLIENT_ID"),
    authority=f"https://login.microsoftonline.com/{os.getenv('TENANT_ID')}",
    client_credential=os.getenv("CLIENT_SECRET"))
tok = app.acquire_token_for_client(scopes=[f"{GRAPH}/.default"])
h={"Authorization":f"Bearer {tok['access_token']}"}

# Recently created Unified groups that became Teams
url = f"{API}/groups?$filter=groupTypes/any(x:x eq 'Unified') and resourceProvisioningOptions/any(x:x eq 'Team')&$select=id,displayName,createdDateTime,resourceProvisioningOptions&$orderby=createdDateTime desc&$top=15"
r=requests.get(url,headers=h,timeout=60); print("=>", r.status_code)
for g in r.json().get("value", []):
    print(f"- {g['createdDateTime']}  id:{g['id']}  name:{g['displayName']}  RPO:{g.get('resourceProvisioningOptions',[])}")
