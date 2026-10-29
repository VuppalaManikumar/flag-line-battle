#!/usr/bin/env python3
"""
Facebook Page Quick Connection Tool.
Validates your Page ID and Page Access Token and saves them to facebook_config.json.
"""

import os
import sys
import json
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "facebook_config.json")

def main():
    print("=" * 65)
    print("🔗 FACEBOOK PAGE QUICK CONNECT")
    print("=" * 65)
    print("\nNeed help getting your token?")
    print("👉 Open Meta Graph API Explorer: https://developers.facebook.com/tools/explorer/\n")

    page_id = input("1. Enter your Facebook Page ID: ").strip()
    token = input("2. Enter your Page Access Token: ").strip()

    if not page_id or not token:
        print("\n❌ Error: Neither Page ID nor Token can be empty!")
        input("\nPress Enter to exit...")
        return

    print("\n⏳ Testing connection with Facebook servers...")
    url = f"https://graph.facebook.com/v19.0/{page_id}?fields=name,id,category,link&access_token={token}"
    
    try:
        res = requests.get(url, timeout=12)
        data = res.json()
    except Exception as e:
        print(f"\n❌ Network error: {e}")
        input("\nPress Enter to exit...")
        return

    if "error" in data:
        err_msg = data["error"].get("message", "Unknown error")
        print(f"\n❌ Connection failed! Meta returned:")
        print(f"   {err_msg}")
        print("\nTips:")
        print("  - Make sure you selected YOUR PAGE in the 'User or Page' dropdown in Graph API Explorer.")
        print("  - Verify that 'pages_manage_posts' permission is added.")
        input("\nPress Enter to exit...")
        return

    page_name = data.get("name", "Unknown Page")
    print("\n" + "=" * 65)
    print(f"🎉 CONNECTED SUCCESSFULLY TO:")
    print(f"   Page Name : {page_name}")
    print(f"   Page ID   : {data.get('id')}")
    print(f"   Category  : {data.get('category', 'N/A')}")
    print("=" * 65)

    # Load existing config or create new
    config = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            config = {}

    config["facebook_page_id"] = page_id
    config["facebook_page_access_token"] = token
    config["videos_per_day"] = 3
    config["post_as_reels"] = True
    config["auto_schedule"] = True
    config["schedule_target_hours"] = [10, 15, 20]
    if "hashtags" not in config:
        config["hashtags"] = [
            "#FlagBattle", "#CountryBattle", "#FlagWar", "#Reels",
            "#OddlySatisfying", "#ViralVideo", "#Gaming", "#Simulation",
            "#Shorts", "#FYP"
        ]

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(f"\n✅ Settings saved to: {CONFIG_PATH}")
    print("👉 You can now run 'schedule_7_days.bat' to schedule 21 videos automatically!")
    input("\nPress Enter to finish...")

if __name__ == "__main__":
    main()
