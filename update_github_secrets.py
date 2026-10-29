#!/usr/bin/env python3
"""
Helper script to update GitHub Secrets and local configuration with a fresh Meta Page Access Token.
"""

import sys
import json
import subprocess
import requests
from base64 import b64encode

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    from nacl import encoding, public
except ImportError:
    print("PyNaCl is required. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pynacl"], check=True)
    from nacl import encoding, public

OWNER = "VuppalaManikumar"
REPO = "flag-line-battle"
CONFIG_PATH = "facebook_config.json"

def get_github_token() -> str:
    p = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n', text=True, capture_output=True)
    creds = dict(line.split('=', 1) for line in p.stdout.splitlines() if '=' in line)
    return creds.get('password', '')

def set_github_secret(gh_token: str, secret_name: str, secret_value: str) -> bool:
    headers = {'Authorization': f'Bearer {gh_token}', 'Accept': 'application/vnd.github.v3+json'}
    r = requests.get(f'https://api.github.com/repos/{OWNER}/{REPO}/actions/secrets/public-key', headers=headers)
    if r.status_code != 200:
        print(f"Error fetching repo public key: {r.status_code} {r.text}")
        return False
        
    pub_data = r.json()
    key_id = pub_data['key_id']
    pub_key_b64 = pub_data['key']

    public_key_obj = public.PublicKey(pub_key_b64.encode('utf-8'), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key_obj)
    encrypted = sealed_box.encrypt(secret_value.encode('utf-8'))
    enc_val = b64encode(encrypted).decode('utf-8')

    put_url = f'https://api.github.com/repos/{OWNER}/{REPO}/actions/secrets/{secret_name}'
    res = requests.put(put_url, json={'encrypted_value': enc_val, 'key_id': key_id}, headers=headers)
    return res.status_code in (201, 204)

def main():
    print("=" * 65)
    print("🔑 UPDATE FACEBOOK PAGE TOKEN (LOCAL & GITHUB ACTIONS)")
    print("=" * 65)
    
    token = input("\n👉 Paste your fresh Facebook Page Access Token: ").strip()
    if not token:
        print("Token cannot be empty.")
        return

    page_id = "1405394435990645"
    
    # Verify token
    print("\n🔍 Validating token with Meta Graph API...")
    url = f"https://graph.facebook.com/v19.0/{page_id}?fields=name,id&access_token={token}"
    res = requests.get(url).json()
    
    if "error" in res:
        print(f"❌ Token validation failed: {res['error'].get('message')}")
        print("Please generate a valid Page Access Token from Graph API Explorer.")
        return

    page_name = res.get("name", "Daily Flag Battles")
    print(f"✅ Token Verified! Connected to Facebook Page: '{page_name}' (ID: {page_id})")

    # Update local facebook_config.json
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
        
    cfg["facebook_page_id"] = page_id
    cfg["facebook_page_access_token"] = token
    cfg["videos_per_day"] = 10
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    print("✅ Updated local facebook_config.json")

    # Update GitHub Secrets
    gh_token = get_github_token()
    if gh_token:
        print("\n☁️ Syncing secret to GitHub Actions repository...")
        ok = set_github_secret(gh_token, "FB_PAGE_ACCESS_TOKEN", token)
        if ok:
            print(f"✅ Updated GitHub Secret 'FB_PAGE_ACCESS_TOKEN' on {OWNER}/{REPO}!")
        else:
            print("⚠️ Could not update GitHub Secret automatically. You can set it in repo Settings -> Secrets.")
    else:
        print("⚠️ GitHub credentials not found in Git Credential Manager.")

    print("\n🎉 Setup Complete! GitHub Actions will now generate & post 10 Reels daily on 100% autopilot!")

if __name__ == "__main__":
    main()
