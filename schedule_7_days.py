#!/usr/bin/env python3
"""
7-Day Automated Facebook Scheduler for Flag Line Battle.
Generates and automatically schedules 21 viral videos (3 per day for 7 days)
directly to your Facebook Page as Reels.
"""

import os
import sys
import json
import time
import random
import datetime
from typing import List, Dict, Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from countries import COUNTRY_DATABASE
from video_builder import generate_battle_video, OUTPUT_DIR
from fb_uploader import (
    generate_caption,
    get_7_day_schedule_timestamps,
    test_credentials,
    upload_reel_to_facebook
)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "facebook_config.json")
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "facebook_posts.log")

def load_or_setup_config() -> Dict[str, Any]:
    """Loads config, prompting user interactively if credentials are missing."""
    config = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            config = {}
            
    page_id = config.get("facebook_page_id", "").strip()
    token = config.get("facebook_page_access_token", "").strip()
    
    # Check if credentials are valid
    is_valid, msg = test_credentials(page_id, token)
    if is_valid:
        print(f"✅ {msg}")
        return config

    # If invalid or placeholder, prompt user in console
    print("\n" + "=" * 65)
    print("🔑 CONNECT YOUR FACEBOOK PAGE (ONE-TIME SETUP)")
    print("=" * 65)
    print("To schedule 21 videos automatically across the next 7 days,")
    print("we need your Facebook Page ID and Page Access Token.")
    print("Get your token here: https://developers.facebook.com/tools/explorer/")
    print("-" * 65)
    
    while True:
        user_page_id = input("\n👉 Enter your Facebook Page ID (e.g. 102938475619283): ").strip()
        user_token = input("👉 Enter your Page Access Token: ").strip()
        
        if not user_page_id or not user_token:
            print("⚠️ Page ID and Token cannot be blank. Please try again.")
            continue
            
        print("\n🔍 Verifying credentials with Facebook Meta servers...")
        valid, status = test_credentials(user_page_id, user_token)
        if valid:
            print(f"🎉 Success! {status}")
            config["facebook_page_id"] = user_page_id
            config["facebook_page_access_token"] = user_token
            config["videos_per_day"] = 3
            config["post_as_reels"] = True
            config["auto_schedule"] = True
            config["schedule_target_hours"] = [10, 15, 20]
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            print(f"💾 Saved to {CONFIG_PATH}!")
            return config
        else:
            print(f"❌ Verification failed: {status}")
            print("Tips:")
            print("  1. Make sure you selected YOUR PAGE in Graph API Explorer (not 'User Token').")
            print("  2. Ensure permissions 'pages_manage_posts' and 'pages_read_engagement' are checked.")
            retry = input("\nWould you like to try entering the token again? (Y/N): ").strip().lower()
            if retry != 'y':
                print("\n⚠️ Proceeding in offline generation mode (videos will be saved locally without upload).")
                config["facebook_page_id"] = "OFFLINE"
                config["facebook_page_access_token"] = "OFFLINE"
                return config

def log_post(message: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def run_7_day_scheduler():
    print("\n" + "=" * 70)
    print("🚀 FLAG LINE BATTLE - 7-DAY AUTOMATIC FACEBOOK SCHEDULER")
    print("📅 Total Days: 7 Days | Videos Per Day: 3 | Total Videos: 21 Reels")
    print("=" * 70 + "\n")

    config = load_or_setup_config()
    page_id = config.get("facebook_page_id", "")
    access_token = config.get("facebook_page_access_token", "")
    is_live_upload = (page_id not in ("OFFLINE", "YOUR_PAGE_ID_HERE") and access_token not in ("OFFLINE", "YOUR_PAGE_ACCESS_TOKEN_HERE"))

    target_hours = config.get("schedule_target_hours", [10, 15, 20])
    hashtags = config.get("hashtags", None)

    # Calculate all 21 scheduling slots across 7 days
    slots = get_7_day_schedule_timestamps(days=7, target_hours=target_hours)
    total_videos = len(slots)
    
    print(f"\n📅 Generated 21 Scheduling Slots:")
    for s in slots[:3]:
        print(f"   • Day {s['day_number']}: {s['readable']}")
    print(f"   ... and so on through Day 7 ({slots[-1]['readable']})\n")

    all_countries = list(COUNTRY_DATABASE.keys())
    manifest_path = os.path.join(OUTPUT_DIR, "7_day_schedule_manifest.txt")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(manifest_path, "w", encoding="utf-8") as mf:
        mf.write(f"=== FLAG LINE BATTLE - 7-DAY SCHEDULE MANIFEST ===\n")
        mf.write(f"Created on: {datetime.datetime.now().strftime('%Y-%m-%d %I:%M %p')}\n")
        mf.write(f"Total Videos: 21 Reels (3 per day for 7 days)\n\n")

    successful_schedules = 0
    t_start = time.time()

    for idx, slot in enumerate(slots):
        num = idx + 1
        day_num = slot["day_number"]
        sched_time = slot["timestamp"]
        sched_str = slot["readable"]

        print("\n" + "=" * 65)
        print(f"🎬 [VIDEO {num}/21] Day {day_num} of 7 | Scheduled for: {sched_str}")
        print("=" * 65)

        # Pick 3 or 4 random countries
        k = random.choice([3, 4])
        selected_countries = random.sample(all_countries, k)

        video_path, countries_list, winner = generate_battle_video(
            countries=selected_countries,
            total_lines=30,
            intro_duration=4.8,
            return_meta=True
        )

        caption = generate_caption(countries_list, winner, custom_hashtags=hashtags)
        filename = os.path.basename(video_path)

        # Upload & schedule to Facebook
        if is_live_upload:
            ok, upload_msg = upload_reel_to_facebook(
                video_path=video_path,
                caption=caption,
                page_id=page_id,
                access_token=access_token,
                scheduled_timestamp=sched_time
            )
            status_text = f"SUCCESS: {upload_msg}" if ok else f"FAILED: {upload_msg}"
            if ok:
                successful_schedules += 1
            print(f"📢 [{num}/21] {status_text}")
            log_post(f"Video {num}/21 ({filename}) [Day {day_num}]: {upload_msg}")
        else:
            status_text = "SAVED LOCALLY (Offline mode)"
            successful_schedules += 1
            print(f"📦 [{num}/21] Saved locally: {filename}")

        # Update Manifest file
        with open(manifest_path, "a", encoding="utf-8") as mf:
            mf.write(f"--- [Video {num}/21] Day {day_num}: {sched_str} ---\n")
            mf.write(f"File: {filename}\n")
            mf.write(f"Matchup: {' vs '.join(countries_list)} | Winner: {winner}\n")
            mf.write(f"Status: {status_text}\n")
            mf.write(f"Caption:\n{caption}\n\n")

    total_time_min = (time.time() - t_start) / 60.0
    print("\n" + "=" * 70)
    print("🎉 7-DAY AUTOMATION PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"⏱️ Total time taken: {total_time_min:.1f} minutes")
    print(f"📊 Scheduled: {successful_schedules} of 21 Reels")
    print(f"📝 Full schedule manifest saved in: {manifest_path}")
    print(f"📁 Video files saved in: {OUTPUT_DIR}")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    run_7_day_scheduler()
