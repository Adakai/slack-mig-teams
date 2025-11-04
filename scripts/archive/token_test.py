import os
from msal import ConfidentialClientApplication

tenant = os.getenv("TENANT_ID")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

missing = [
    k
    for k, v in {
        "TENANT_ID": tenant,
        "CLIENT_ID": client_id,
        "CLIENT_SECRET": client_secret,
    }.items()
    if not v
]
if missing:
    raise SystemExit(f"Missing env(s): {', '.join(missing)}. Check your .env.")

app = ConfidentialClientApplication(
    client_id=client_id,
    client_credential=client_secret,
    authority=f"https://login.microsoftonline.com/{tenant}",
)

result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
if "access_token" not in result:
    raise SystemExit(f"Token failure: {result}")

print("✅ Got app-only token. Expires in (s):", result.get("expires_in"))
