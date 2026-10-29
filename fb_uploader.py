import os
import sys
import json
import time
import random
import datetime
from typing import List, Optional, Tuple, Dict, Any
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

COUNTRY_EMOJIS = {
    "Germany": "🇩🇪", "Austria": "🇦🇹", "Ireland": "🇮🇪", "Netherlands": "🇳🇱",
    "Greece": "🇬🇷", "France": "🇫🇷", "Brazil": "🇧🇷", "Argentina": "🇦🇷",
    "United States": "🇺🇸", "United Kingdom": "🇬🇧", "Japan": "🇯🇵",
    "South Korea": "🇰🇷", "India": "🇮🇳", "Canada": "🇨🇦", "Italy": "🇮🇹",
    "Spain": "🇪🇸", "Portugal": "🇵🇹", "Sweden": "🇸🇪", "Norway": "🇳🇴",
    "Denmark": "🇩🇰", "Finland": "🇫🇮", "Switzerland": "🇨🇭", "Belgium": "🇧🇪",
    "Poland": "🇵🇱", "Australia": "🇦🇺", "Mexico": "🇲🇽", "Turkey": "🇹🇷",
    "Egypt": "🇪🇬", "South Africa": "🇿🇦", "Morocco": "🇲🇦"
}

HOOKS = [
    "Who takes the crown today?! Drop your country below! 👇",
    "Only 1 flag can survive this laser arena! Who are you supporting? ⚔️",
    "Watch until the end... You won't believe which country survived! 😱",
    "Which country has the strongest defense?! Vote in the comments! 🏆",
    "Flag Battle Royale! Can your favorite country win this? 👑"
]

def generate_caption(countries: List[str], winner_name: str, custom_hashtags: Optional[List[str]] = None) -> str:
    """Generates a high-retention viral caption with emojis, country matchups, and hashtags."""
    c_with_emojis = [f"{COUNTRY_EMOJIS.get(c, '🏳️')} {c}" for c in countries]
    vs_title = " VS ".join(c_with_emojis)
    hook = random.choice(HOOKS)
    winner_emoji = COUNTRY_EMOJIS.get(winner_name, "👑")
    
    default_tags = [
        "#FlagBattle", "#CountryBattle", "#FlagWar", "#Reels",
        "#OddlySatisfying", "#ViralVideo", "#Gaming", "#Simulation",
        "#Shorts", "#FYP", "#WorldCup"
    ]
    tags = custom_hashtags if custom_hashtags else default_tags
    tags_str = " ".join(tags)
    
    caption = (
        f"🔥 {vs_title} 🔥\n\n"
        f"{hook}\n\n"
        f"🏆 WINNER: {winner_emoji} {winner_name.upper()}!\n"
        f"👉 Drop your favorite country in the comments!\n"
        f"❤️ Like & Follow for daily country battles!\n\n"
        f"{tags_str}"
    )
    return caption

DEFAULT_10_SLOTS = [
    "08:00", "09:30", "11:00", "12:30", "14:00",
    "15:30", "17:00", "18:30", "20:00", "21:30"
]

def parse_slot_time(slot_val: Any) -> Tuple[int, int]:
    """Parses '08:00', 8, 8.5, or (8, 30) into (hour, minute)."""
    if isinstance(slot_val, str):
        if ":" in slot_val:
            parts = slot_val.split(":")
            return int(parts[0]), int(parts[1])
        return int(slot_val), 0
    elif isinstance(slot_val, (int, float)):
        h = int(slot_val)
        m = int(round((slot_val - h) * 60))
        return h, m
    elif isinstance(slot_val, (list, tuple)):
        return int(slot_val[0]), int(slot_val[1])
    return 12, 0

def get_schedule_timestamps(
    count: int = 10,
    target_hours: Optional[List[Any]] = None,
    timezone_name: str = "Asia/Kolkata"
) -> List[Optional[int]]:
    """
    Calculates unix timestamps to schedule posts across the day.
    Facebook API requires scheduled posts to be at least 10 minutes in the future.
    Uses target timezone (default Asia/Kolkata) so scheduling aligns with peak viewer activity.
    If a slot for today has already passed, it schedules for tomorrow at that slot time.
    """
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(timezone_name)
    except Exception:
        tz = None

    now = datetime.datetime.now(tz) if tz else datetime.datetime.now()

    target_slots = target_hours
    if not target_slots:
        if count >= 10:
            target_slots = DEFAULT_10_SLOTS
        elif count == 3:
            target_slots = ["10:00", "15:00", "20:00"]
        else:
            start_min = 8 * 60
            end_min = 22 * 60
            step = (end_min - start_min) / max(1, count - 1) if count > 1 else 0
            target_slots = []
            for i in range(count):
                total_m = int(start_min + i * step)
                target_slots.append(f"{total_m // 60:02d}:{total_m % 60:02d}")

    scheduled_dts = []
    for i in range(count):
        slot_raw = target_slots[i % len(target_slots)]
        h, m = parse_slot_time(slot_raw)
        today_slot = now.replace(hour=h, minute=m, second=0, microsecond=0)

        # Meta requires scheduled posts to be at least 10-20 minutes in the future
        if today_slot > now + datetime.timedelta(minutes=20):
            scheduled_dts.append(today_slot)
        else:
            tomorrow_slot = today_slot + datetime.timedelta(days=1)
            scheduled_dts.append(tomorrow_slot)

    scheduled_dts.sort()
    return [int(dt.timestamp()) for dt in scheduled_dts]

def get_7_day_schedule_timestamps(
    days: int = 7,
    target_hours: Optional[List[Any]] = None,
    timezone_name: str = "Asia/Kolkata"
) -> List[Dict[str, Any]]:
    """
    Generates exact scheduled publishing timestamps across N days.
    """
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(timezone_name)
    except Exception:
        tz = None

    now = datetime.datetime.now(tz) if tz else datetime.datetime.now()
    slots_per_day = target_hours if target_hours else DEFAULT_10_SLOTS
    
    slots = []
    for day_offset in range(days):
        day_date = now.date() + datetime.timedelta(days=day_offset)
        for s in slots_per_day:
            h, m = parse_slot_time(s)
            slot_dt = datetime.datetime.combine(day_date, datetime.time(hour=h, minute=m, second=0))
            if tz:
                slot_dt = slot_dt.replace(tzinfo=tz)
                
            if slot_dt < now + datetime.timedelta(minutes=20):
                slot_dt = now + datetime.timedelta(minutes=25 + len(slots) * 90)
                
            slots.append({
                "day_number": day_offset + 1,
                "datetime": slot_dt,
                "timestamp": int(slot_dt.timestamp()),
                "readable": slot_dt.strftime("%A, %b %d at %I:%M %p")
            })
    return slots

def test_credentials(page_id: str, access_token: str) -> Tuple[bool, str]:
    """Tests if the provided Facebook Page ID and Access Token are valid."""
    if not page_id or page_id == "YOUR_PAGE_ID_HERE" or not access_token or access_token == "YOUR_PAGE_ACCESS_TOKEN_HERE":
        return False, "Placeholder credentials detected in facebook_config.json."
        
    url = f"https://graph.facebook.com/v19.0/{page_id}?fields=name,id&access_token={access_token}"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if "error" in data:
            return False, data["error"].get("message", "Unknown Facebook API error.")
        return True, f"Connected to Facebook Page: '{data.get('name')}' (ID: {data.get('id')})"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

def upload_reel_to_facebook(
    video_path: str,
    caption: str,
    page_id: str,
    access_token: str,
    scheduled_timestamp: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Uploads a video to a Facebook Page as a Facebook Reel using the official 3-phase Reels API.
    Supports immediate publish or scheduled publishing.
    """
    if not os.path.exists(video_path):
        return False, f"Video file not found: {video_path}"

    file_size = os.path.getsize(video_path)
    base_url = f"https://graph.facebook.com/v19.0/{page_id}/video_reels"

    print(f"\n[Facebook Upload] Initiating Reel upload for {os.path.basename(video_path)} ({file_size / (1024*1024):.2f} MB)...")

    # Step 1: Initialize Upload Session
    init_payload = {
        "upload_phase": "start",
        "access_token": access_token
    }
    try:
        init_res = requests.post(base_url, data=init_payload, timeout=20)
        init_data = init_res.json()
    except Exception as e:
        return False, f"Step 1 (Init) Network error: {e}"

    if "video_id" not in init_data or "upload_url" not in init_data:
        err = init_data.get("error", {}).get("message", str(init_data))
        return False, f"Step 1 (Init) Failed: {err}"

    video_id = init_data["video_id"]
    upload_url = init_data["upload_url"]
    print(f"   [Step 1] Initialized session! Video ID: {video_id}")

    # Step 2: Upload Binary Video Data
    print(f"   [Step 2] Transferring video bytes to Meta servers...")
    headers = {
        "Authorization": f"OAuth {access_token}",
        "offset": "0",
        "file_size": str(file_size)
    }
    try:
        with open(video_path, "rb") as video_file:
            upload_res = requests.post(upload_url, headers=headers, data=video_file, timeout=120)
            upload_data = upload_res.json()
    except Exception as e:
        return False, f"Step 2 (Upload) Network error: {e}"

    if not upload_data.get("success", False) and "video_id" not in upload_data:
        err = upload_data.get("error", {}).get("message", str(upload_data))
        return False, f"Step 2 (Upload) Failed: {err}"

    print(f"   [Step 2] Video bytes uploaded successfully!")

    # Step 3: Publish or Schedule the Reel
    finish_payload = {
        "upload_phase": "finish",
        "access_token": access_token,
        "video_id": video_id,
        "description": caption
    }

    if scheduled_timestamp:
        finish_payload["video_state"] = "SCHEDULED"
        finish_payload["scheduled_publish_time"] = str(scheduled_timestamp)
        sched_readable = datetime.datetime.fromtimestamp(scheduled_timestamp).strftime('%Y-%m-%d %I:%M %p')
        print(f"   [Step 3] Finalizing & scheduling publication for: {sched_readable}...")
    else:
        finish_payload["video_state"] = "PUBLISHED"
        print(f"   [Step 3] Finalizing & publishing Reel immediately...")

    try:
        finish_res = requests.post(base_url, data=finish_payload, timeout=25)
        finish_data = finish_res.json()
    except Exception as e:
        return False, f"Step 3 (Finish) Network error: {e}"

    if finish_data.get("success", False) or "video_id" in finish_data:
        post_id = finish_data.get("id", video_id)
        return True, f"Reel successfully published/scheduled! Post ID: {post_id}"
    else:
        err = finish_data.get("error", {}).get("message", str(finish_data))
        return False, f"Step 3 (Finish) Failed: {err}"
