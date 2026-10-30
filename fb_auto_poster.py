#!/usr/bin/env python3
"""
Facebook Auto-Poster for Flag Line Battle.
Generates 10 viral videos per day and automatically uploads/schedules them to your Facebook Page as Reels.
Runs headlessly and fully automated on GitHub Actions or locally.
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
    get_schedule_timestamps,
    test_credentials,
    upload_reel_to_facebook
)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "facebook_config.json")
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "facebook_posts.log")
STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")

DEFAULT_SLOTS = [
    "08:00", "09:30", "11:00", "12:30", "14:00",
    "15:30", "17:00", "18:30", "20:00", "21:30"
]

def load_state() -> Dict[str, Any]:
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_state(state: Dict[str, Any]):
    try:
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error saving state: {e}")

def load_config() -> Dict[str, Any]:
    """Loads configuration from environment variables or facebook_config.json."""
    default_config = {
        "facebook_page_id": os.environ.get("FACEBOOK_PAGE_ID", "").strip(),
        "facebook_page_access_token": os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip(),
        "videos_per_day": int(os.environ.get("VIDEOS_PER_DAY", "10")),
        "post_as_reels": True,
        "auto_schedule": True,
        "schedule_timezone": os.environ.get("SCHEDULE_TIMEZONE", "Asia/Kolkata"),
        "schedule_target_slots": DEFAULT_SLOTS,
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
    if os.environ.get("VIDEOS_PER_DAY"):
        try:
            default_config["videos_per_day"] = int(os.environ.get("VIDEOS_PER_DAY"))
        except ValueError:
            pass

    return default_config

def log_post(message: str):
    """Appends status line to facebook_posts.log."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}\n"
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass

def run_daily_poster(count_override: Optional[int] = None, immediate: bool = False, cleanup: bool = False, force: bool = False):
    print("\n" + "=" * 70)
    print("🚀 FLAG LINE BATTLE - FULLY AUTOMATED 10x REELS AUTO-POSTER")
    print("=" * 70)
    
    config = load_config()
    page_id = config.get("facebook_page_id", "").strip()
    access_token = config.get("facebook_page_access_token", "").strip()
    target_count = count_override if count_override is not None else int(config.get("videos_per_day", 10))
    auto_schedule = not immediate and config.get("auto_schedule", True)
    target_slots = config.get("schedule_target_slots", DEFAULT_SLOTS)
    timezone_name = config.get("schedule_timezone", "Asia/Kolkata")
    hashtags = config.get("hashtags", None)
    is_ci = os.environ.get("GITHUB_ACTIONS") == "true" or cleanup

    print(f"🎯 Target Volume: {target_count} Reels per day")
    print(f"🕒 Timezone: {timezone_name}")
    print(f"🤖 Environment: {'GitHub Actions (Cloud CI)' if os.environ.get('GITHUB_ACTIONS') == 'true' else 'Local System'}")

    # Check if already fulfilled today
    today_str = datetime.date.today().isoformat()
    state = load_state()
    if not force and state.get("last_date") == today_str and state.get("successful_uploads", 0) >= target_count:
        print(f"\n✅ Today's {target_count} Reels have ALREADY been scheduled for {today_str}!")
        print("Meta is publishing each video across the 10 peak slots throughout the day.")
        print("Use --force to run an extra batch.\n")
        return

    # 1. Test credentials
    is_valid, status_msg = test_credentials(page_id, access_token)
    print(f"📊 Facebook Connection: {status_msg}")
    
    if not is_valid:
        print("\n" + "!" * 70)
        print("⚠️  FACEBOOK CREDENTIALS NOT AVAILABLE OR EXPIRED!")
        print("!" * 70)
        print("Set FACEBOOK_PAGE_ID and a valid FACEBOOK_PAGE_ACCESS_TOKEN.")
        print(f"Proceeding in simulation/local-render mode for {target_count} videos...")
        print("=" * 70 + "\n")

    # 2. Calculate schedule times
    if is_valid and auto_schedule:
        schedule_timestamps = get_schedule_timestamps(target_count, target_slots, timezone_name)
    else:
        schedule_timestamps = [None] * target_count

    all_countries = list(COUNTRY_DATABASE.keys())
    generated_records = []
    
    # 3. Generate the videos
    for i in range(target_count):
        print(f"\n" + "-" * 60)
        print(f"🎬 [VIDEO {i + 1} OF {target_count}] Generating Battle Royale Video...")
        print("-" * 60)
        
        k = random.choice([3, 4])
        selected = random.sample(all_countries, k)
        
        video_path, countries_list, winner = generate_battle_video(
            countries=selected,
            total_lines=30,
            intro_duration=4.8,
            return_meta=True
        )
        
        caption = generate_caption(countries_list, winner, custom_hashtags=hashtags)
        sched_time = schedule_timestamps[i]
        
        generated_records.append({
            "video_path": video_path,
            "countries": countries_list,
            "winner": winner,
            "caption": caption,
            "scheduled_time": sched_time
        })

    # 4. Upload / Schedule each video to Facebook
    print("\n" + "=" * 70)
    print(f"📤 UPLOADING & SCHEDULING {len(generated_records)} REELS TO FACEBOOK")
    print("=" * 70)

    captions_file_path = os.path.join(OUTPUT_DIR, "today_captions.txt")
    try:
        with open(captions_file_path, "w", encoding="utf-8") as cap_file:
            cap_file.write(f"=== TODAY'S FACEBOOK REELS ({datetime.date.today()}) ===\n\n")
    except Exception:
        pass

    successful_uploads = 0

    for idx, rec in enumerate(generated_records):
        vid_num = idx + 1
        path = rec["video_path"]
        caption = rec["caption"]
        sched = rec["scheduled_time"]
        
        sched_str = datetime.datetime.fromtimestamp(sched).strftime('%Y-%m-%d %I:%M %p') if sched else 'Immediate'

        try:
            with open(captions_file_path, "a", encoding="utf-8") as cap_file:
                cap_file.write(f"--- VIDEO {vid_num} (Scheduled: {sched_str}) ---\n")
                cap_file.write(f"File: {os.path.basename(path)}\n")
                cap_file.write(f"Caption:\n{caption}\n\n")
        except Exception:
            pass

        if is_valid:
            print(f"\n🚀 Posting Reel [{vid_num}/{target_count}] -> Slot: {sched_str}")
            ok, upload_msg = upload_reel_to_facebook(
                video_path=path,
                caption=caption,
                page_id=page_id,
                access_token=access_token,
                scheduled_timestamp=sched
            )
            print(f"   Status: {upload_msg}")
            log_post(f"Video {vid_num} ({os.path.basename(path)}): {upload_msg}")
            if ok:
                successful_uploads += 1
                if is_ci and os.path.exists(path):
                    try:
                        os.remove(path)
                        print(f"   [Cleanup] Local video removed to conserve cloud disk space.")
                    except Exception:
                        pass
        else:
            print(f"[{vid_num}/{target_count}] Video ready: {os.path.basename(path)} (Output folder)")

    # Save state
    save_state({
        "last_date": today_str,
        "last_run_timestamp": int(time.time()),
        "target_count": target_count,
        "successful_uploads": successful_uploads,
        "is_valid": is_valid
    })

    print("\n" + "=" * 70)
    print("🎉 DAILY AUTOMATION BATCH COMPLETE!")
    print("=" * 70)
    if is_valid:
        print(f"✅ {successful_uploads}/{target_count} Facebook Reels successfully uploaded & scheduled!")
        print("Meta will automatically publish each Reel at its designated time!")
    else:
        print(f"📁 {len(generated_records)} videos generated locally in: {OUTPUT_DIR}")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flag Line Battle 10x Daily Auto-Poster")
    parser.add_argument("--count", type=int, default=None, help="Number of reels to generate and post (default: 10)")
    parser.add_argument("--immediate", action="store_true", help="Post immediately instead of scheduling")
    parser.add_argument("--cleanup", action="store_true", help="Delete local video files after upload")
    parser.add_argument("--force", action="store_true", help="Force generation even if already completed today")
    args = parser.parse_args()

    run_daily_poster(count_override=args.count, immediate=args.immediate, cleanup=args.cleanup, force=args.force)
