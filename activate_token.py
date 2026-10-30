#!/usr/bin/env python3
"""
Interactive or CLI helper to connect a fresh Meta Access Token,
test Reel upload capability, sync to GitHub Secrets, and trigger the cloud autopilot.
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
    subprocess.run([sys.executable, "-m", "pip", "install", "pynacl"], check=True)
    from nacl import encoding, public

OWNER = "VuppalaManikumar"
REPO = "flag-line-battle"
CONFIG_PATH = "facebook_config.json"
TARGET_PAGE_NAME = "Daily Flag Battles"
TARGET_PAGE_ID = "1405394435990645"

def get_github_token() -> str:
    p = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n', text=True, capture_output=True)
    creds = dict(line.split('=', 1) for line in p.stdout.splitlines() if '=' in line)
    return creds.get('password', '')

def set_github_secret(gh_token: str, secret_name: str, secret_value: str) -> bool:
    headers = {'Authorization': f'Bearer {gh_token}', 'Accept': 'application/vnd.github.v3+json'}
    r = requests.get(f'https://api.github.com/repos/{OWNER}/{REPO}/actions/secrets/public-key', headers=headers)
    if r.status_code != 200:
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

def trigger_github_workflow(gh_token: str):
    headers = {'Authorization': f'Bearer {gh_token}', 'Accept': 'application/vnd.github.v3+json'}
    url = f'https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/400336386/dispatches'
    res = requests.post(url, json={'ref': 'main', 'inputs': {'count': '10', 'force': True}}, headers=headers)
    return res.status_code == 204

def activate(raw_token: str):
    token = raw_token.strip()
    if not token:
        print("❌ Token cannot be empty.")
        return False

    print("\n🔍 Step 1: Validating token with Meta Graph API...")
    # Check if this token is a User token or Page token
    url_me = f"https://graph.facebook.com/v19.0/me?fields=name,id&access_token={token}"
    me_res = requests.get(url_me).json()
    
    if "error" in me_res:
        print(f"❌ Token validation failed: {me_res['error'].get('message')}")
        return False

    print(f"   Authenticated as: {me_res.get('name')} (ID: {me_res.get('id')})")

    # Check /me/accounts to find Page tokens
    url_acc = f"https://graph.facebook.com/v19.0/me/accounts?access_token={token}"
    acc_res = requests.get(url_acc).json()
    pages = acc_res.get("data", [])

    page_id = None
    page_token = None
    page_name = None

    if pages:
        print(f"\n📄 Found {len(pages)} Facebook Page(s) managed by this account:")
        target_found = None
        for p in pages:
            print(f"   - {p.get('name')} (ID: {p.get('id')})")
            if p.get("id") == TARGET_PAGE_ID or TARGET_PAGE_NAME.lower() in p.get("name", "").lower():
                target_found = p

        if target_found:
            page_id = target_found.get("id")
            page_token = target_found.get("access_token")
            page_name = target_found.get("name")
            print(f"   🎯 Auto-selected target page: '{page_name}' (ID: {page_id})")
        else:
            # Pick first
            page_id = pages[0].get("id")
            page_token = pages[0].get("access_token")
            page_name = pages[0].get("name")
            print(f"   🎯 Selected: '{page_name}' (ID: {page_id})")
    else:
        # Check if the provided token is directly a Page Token
        url_page = f"https://graph.facebook.com/v19.0/{TARGET_PAGE_ID}?fields=name,id,can_post&access_token={token}"
        p_res = requests.get(url_page).json()
        if "id" in p_res:
            page_id = p_res.get("id")
            page_token = token
            page_name = p_res.get("name", TARGET_PAGE_NAME)
            print(f"   🎯 Verified as direct Page Token for '{page_name}' (ID: {page_id})!")
        else:
            # Fallback to checking the token itself
            page_id = TARGET_PAGE_ID
            page_token = token
            page_name = TARGET_PAGE_NAME

    # Step 2: Test Reel Upload Session initialization
    print("\n🎬 Step 2: Testing Meta Reels Upload Session...")
    url_reels = f"https://graph.facebook.com/v19.0/{page_id}/video_reels"
    r_reels = requests.post(url_reels, data={"upload_phase": "start", "access_token": page_token})
    reels_data = r_reels.json()
    
    if "video_id" in reels_data:
        print(f"   ✅ Reels API Ready! Initialized test session (ID: {reels_data['video_id']})")
    else:
        err = reels_data.get("error", {}).get("message", str(reels_data))
        print(f"   ⚠️ Reels initialization warning: {err}")

    # Step 3: Update local config
    print("\n💾 Step 3: Updating local facebook_config.json...")
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}

    cfg["facebook_page_id"] = page_id
    cfg["facebook_page_access_token"] = page_token
    cfg["page_name"] = page_name
    cfg["videos_per_day"] = 10
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    print("   ✅ Updated facebook_config.json")

    # Step 4: Sync to GitHub Secrets
    print("\n☁️ Step 4: Syncing credentials to GitHub Actions Secrets...")
    gh_token = get_github_token()
    if gh_token:
        ok1 = set_github_secret(gh_token, "FB_PAGE_ID", page_id)
        ok2 = set_github_secret(gh_token, "FB_PAGE_ACCESS_TOKEN", page_token)
        if ok1 and ok2:
            print("   ✅ Synced FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN to GitHub repository!")
            
            print("\n🚀 Step 5: Triggering cloud autopilot batch immediately...")
            ok_trig = trigger_github_workflow(gh_token)
            if ok_trig:
                print("   🎉 Successfully dispatched GitHub Actions! 10 Reels are being created and scheduled right now in the cloud!")
            else:
                print("   ⚠️ Could not trigger workflow dispatch directly, but cron will run automatically.")
        else:
            print("   ⚠️ Could not sync secrets automatically.")
    else:
        print("   ⚠️ GitHub credentials not found.")

    print("\n" + "=" * 65)
    print("🎉 TOKEN ACTIVATION COMPLETE!")
    print("=" * 65)
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        activate(sys.argv[1])
    else:
        print("=" * 65)
        print("🔑 META PAGE ACCESS TOKEN ACTIVATOR")
        print("=" * 65)
        tok = input("👉 Paste your Facebook Access Token: ").strip()
        activate(tok)
