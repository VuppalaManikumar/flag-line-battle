#!/usr/bin/env python3
"""
1-Month (30 Days) Advance Scheduler for Flag Line Battle Facebook Reels.
Generates and automatically schedules 300 viral 1080x1920 60FPS videos
(10 per day across 30 days) directly to your Facebook Page as Reels.
Features auto-resume, rate-limit pacing, and local storage auto-cleanup.
"""

import os
import sys
import json
import time
import random
import argparse
import datetime
from typing import List, Dict, Any, Optional

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
    test_credentials,
    upload_reel_to_facebook
)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "facebook_config.json")
PROGRESS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "month_progress.json")
MANIFEST_PATH = os.path.join(OUTPUT_DIR, "month_schedule_manifest.txt")

DEFAULT_SLOTS = [
    "08:00", "09:30", "11:00", "12:30", "14:00",
    "15:30", "17:00", "18:30", "20:00", "21:30"
]

def load_config() -> Dict[str, Any]:
    default_config = {
        "facebook_page_id": os.environ.get("FACEBOOK_PAGE_ID", "").strip(),
        "facebook_page_access_token": os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip(),
        "page_name": "Daily Flag Battles",
        "hashtags": [
            "#FlagBattle", "#CountryBattle", "#FlagWar", "#Reels",
            "#OddlySatisfying", "#ViralVideo", "#Gaming", "#Simulation",
            "#Shorts", "#FYP"
        ]
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                file_config = json.load(f)
                for k, v in file_config.items():
                    if k not in default_config or not default_config[k]:
                        default_config[k] = v
        except Exception as e:
            print(f"⚠️ Error reading config file: {e}. Using defaults/env.")

    if os.environ.get("FACEBOOK_PAGE_ID"):
        default_config["facebook_page_id"] = os.environ.get("FACEBOOK_PAGE_ID").strip()
    if os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN"):
        default_config["facebook_page_access_token"] = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN").strip()

    return default_config

def load_progress() -> Dict[str, Any]:
    if os.path.exists(PROGRESS_PATH):
        try:
            with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"completed": {}}
    return {"completed": {}}

def save_progress(progress: Dict[str, Any]):
    try:
        with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=2)
    except Exception as e:
        print(f"⚠️ Warning saving progress: {e}")

def generate_slots(days: int = 30, per_day: int = 10, start_day_offset: int = 1, slots_list: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Calculates timestamps for N days ahead."""
    today = datetime.date.today()
    slots = slots_list if slots_list else DEFAULT_SLOTS[:per_day]
    all_slots = []
    
    for day_idx in range(start_day_offset, start_day_offset + days):
        target_date = today + datetime.timedelta(days=day_idx)
        for s_idx, slot_time in enumerate(slots):
            h, m = map(int, slot_time.split(":"))
            dt = datetime.datetime.combine(target_date, datetime.time(hour=h, minute=m, second=0))
            all_slots.append({
                "day_number": day_idx,
                "date": target_date.isoformat(),
                "slot_index": s_idx + 1,
                "slot_time": slot_time,
                "timestamp": int(dt.timestamp()),
                "readable": dt.strftime("%A, %b %d at %I:%M %p")
            })
    return all_slots

def run_month_scheduler(days: int = 30, per_day: int = 10, start_offset: int = 1, cleanup: bool = True):
    print("\n" + "=" * 75)
    print(f"🚀 FLAG LINE BATTLE - 1-MONTH ADVANCE FACEBOOK REELS SCHEDULER")
    print(f"   Target: {days} Days x {per_day} Reels/Day = {days * per_day} Total Videos")
    print("=" * 75)

    config = load_config()
    page_id = config.get("facebook_page_id")
    page_token = config.get("facebook_page_access_token")
    page_name = config.get("page_name", "Daily Flag Battles")
    hashtags = config.get("hashtags", None)

    is_valid, msg = test_credentials(page_id, page_token)
    if not is_valid:
        print(f"❌ Facebook Connection Error: {msg}")
        return

    print(f"✅ Verified Meta Connection: '{page_name}' (ID: {page_id})")

    all_slots = generate_slots(days=days, per_day=per_day, start_day_offset=start_offset)
    total_slots = len(all_slots)

    progress = load_progress()
    completed = progress.get("completed", {})
    already_done = len(completed)

    print(f"📋 Total Slots Planned: {total_slots}")
    print(f"✨ Already Uploaded & Scheduled: {already_done}/{total_slots}")
    print(f"⚡ Remaining to Generate & Post: {total_slots - already_done}\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(MANIFEST_PATH, "a", encoding="utf-8") as manifest:
        manifest.write(f"\n=== 1-MONTH SCHEDULING SESSION STARTED: {datetime.datetime.now()} ===\n")

    all_countries = list(COUNTRY_DATABASE.keys())

    for idx, slot in enumerate(all_slots):
        slot_key = str(slot["timestamp"])
        if slot_key in completed:
            continue

        slot_num = len(completed) + 1
        readable = slot["readable"]
        day_num = slot["day_number"]
        slot_idx = slot["slot_index"]

        print("=" * 70)
        print(f"🎬 [{slot_num}/{total_slots}] Day {day_num} | Reel {slot_idx} -> Scheduled for: {readable}")
        print("=" * 70)

        # 1. Pick 3 or 4 random countries
        k = random.choice([3, 4])
        selected = random.sample(all_countries, k)

        # 2. Render 1080x1920 60FPS video
        video_path, countries_list, winner = generate_battle_video(
            countries=selected,
            total_lines=30,
            intro_duration=4.8,
            return_meta=True
        )

        # 3. Generate viral caption
        caption = generate_caption(countries_list, winner, custom_hashtags=hashtags)

        # 4. Upload and schedule to Meta
        print(f"📤 Uploading Reel to Meta and locking schedule for {readable}...")
        ok, upload_msg = upload_reel_to_facebook(
            video_path=video_path,
            caption=caption,
            page_id=page_id,
            access_token=page_token,
            scheduled_timestamp=slot["timestamp"]
        )

        if ok:
            print(f"✅ SUCCESS: {upload_msg}")
            completed[slot_key] = {
                "day": day_num,
                "date": slot["date"],
                "slot_time": slot["slot_time"],
                "timestamp": slot["timestamp"],
                "readable": readable,
                "winner": winner,
                "countries": countries_list,
                "status": upload_msg,
                "completed_at": datetime.datetime.now().isoformat()
            }
            progress["completed"] = completed
            save_progress(progress)

            with open(MANIFEST_PATH, "a", encoding="utf-8") as manifest:
                manifest.write(f"[{readable}] Day {day_num} Reel {slot_idx}: {winner} won ({' vs '.join(countries_list)}) | {upload_msg}\n")

            # Clean up local video file to save disk space
            if cleanup and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                    print("🧹 [Auto-Cleanup] Local video file removed to save hard drive space.")
                except Exception:
                    pass

            # Gentle pace to respect Meta API rate limits
            time.sleep(3)
        else:
            print(f"⚠️ UPLOAD FAILED: {upload_msg}")
            # If rate limit or temporary error, wait longer
            if "request limit" in upload_msg.lower() or "throttle" in upload_msg.lower():
                print("⏳ Rate limit detected. Resting for 60 seconds...")
                time.sleep(60)
            else:
                time.sleep(5)

    print("\n" + "=" * 75)
    print("🎉🎉 1-MONTH FACEBOOK REELS SCHEDULING COMPLETE! 🎉🎉")
    print(f"Total Videos Scheduled on Meta: {len(completed)}/{total_slots}")
    print(f"Your Facebook Page will publish 10 Reels every single day for the next month!")
    print(f"Manifest saved to: {MANIFEST_PATH}")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="1-Month Advance Facebook Reels Scheduler")
    parser.add_argument("--days", type=int, default=30, help="Number of days to schedule (default: 30)")
    parser.add_argument("--per-day", type=int, default=10, help="Reels per day (default: 10)")
    parser.add_argument("--start-day", type=int, default=1, help="Start day offset: 1 = tomorrow (default: 1)")
    parser.add_argument("--no-cleanup", action="store_true", help="Keep local MP4 files after uploading")
    args = parser.parse_args()

    run_month_scheduler(
        days=args.days,
        per_day=args.per_day,
        start_offset=args.start_day,
        cleanup=not args.no_cleanup
    )
