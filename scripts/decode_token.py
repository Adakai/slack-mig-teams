"""Acquire an app-only token and decode its JWT payload to inspect claims.

Usage:
  pipenv run python .\scripts\decode_token.py

Prints the raw token and a prettified JSON of the payload claims.
"""
import os
import json
import base64
from msal import ConfidentialClientApplication

GRAPH = "https://graph.microsoft.com"

def acquire_token():
    tenant = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    if not all([tenant, client_id, client_secret]):
        print("Missing TENANT_ID/CLIENT_ID/CLIENT_SECRET in environment.")
        raise SystemExit(2)
    app = ConfidentialClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant}",
        client_credential=client_secret,
    )
    tok = app.acquire_token_for_client(scopes=[f"{GRAPH}/.default"]) 
    if "access_token" not in tok:
        print("Token acquisition failed:", tok)
        raise SystemExit(3)
    return tok["access_token"]

def b64url_decode(input_str: str) -> bytes:
    s = input_str
    # pad
    rem = len(s) % 4
    if rem:
        s += '=' * (4 - rem)
    return base64.urlsafe_b64decode(s)

def decode_jwt(token: str):
    parts = token.split('.')
    if len(parts) < 2:
        print('Not a JWT')
        return None
    payload_b64 = parts[1]
    try:
        payload_bytes = b64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode('utf-8'))
        return payload
    except Exception as e:
        print('Failed to decode JWT payload:', e)
        return None

def main():
    tok = acquire_token()
    print('ACCESS_TOKEN:', tok[:200] + '...')
    claims = decode_jwt(tok)
    if claims is None:
        print('Could not decode token claims')
        return
    print('\nDecoded claims:')
    print(json.dumps(claims, indent=2))
    # Helpful quick checks
    print('\nQuick checks:')
    if 'roles' in claims:
        print('  roles:', claims.get('roles'))
    if 'scp' in claims:
        print('  scp:', claims.get('scp'))
    print('  appid:', claims.get('appid') or claims.get('azp'))

if __name__ == '__main__':
    main()
