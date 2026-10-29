#!/usr/bin/env python3
"""
Flag Line Battle - Automatic Video Generator for Facebook Reels / YouTube Shorts / TikTok.
Features:
  - Random 3 or 4 countries selection (or custom countries)
  - 30 initial laser lines per flag
  - Circular arena physics with line cutting, particles & sound effects
  - 1080x1920 60FPS vertical HD video output with synced audio
  - Single or Batch generation for automated social media scheduling
"""

import os
import sys
import argparse
import random
from countries import COUNTRY_DATABASE
from video_builder import generate_battle_video, OUTPUT_DIR

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(
        description="Flag Line Battle Video Generator for Facebook Pages / Reels"
    )
    parser.add_argument(
        "--countries", "-c",
        type=str,
        default=None,
        help="Comma-separated country names (e.g. 'Germany,Austria,Ireland' or 'USA,Brazil,Japan,France')"
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        default=None,
        help="Number of random countries if not specified (default: randomly 3 or 4)"
    )
    parser.add_argument(
        "--lines", "-l",
        type=int,
        default=30,
        help="Number of initial laser lines per country (default: 30)"
    )
    parser.add_argument(
        "--batch", "-b",
        type=int,
        default=1,
        help="Number of distinct videos to generate in batch mode (default: 1)"
    )
    parser.add_argument(
        "--intro", "-i",
        type=float,
        default=4.8,
        help="Duration of random flag selection roulette intro in seconds (default: 4.8s)"
    )
    parser.add_argument(
        "--out", "-o",
        type=str,
        default=None,
        help="Output filename or output directory"
    )
    parser.add_argument(
        "--list-countries",
        action="store_true",
        help="List all available countries in the database"
    )

    args = parser.parse_args()

    if args.list_countries:
        print("\nAvailable Countries:")
        all_c = sorted(list(COUNTRY_DATABASE.keys()))
        for i in range(0, len(all_c), 4):
            chunk = all_c[i:i+4]
            print("  " + ", ".join(f"{c:<16}" for c in chunk))
        print(f"\nTotal: {len(all_c)} countries available.\n")
        return

    all_countries = list(COUNTRY_DATABASE.keys())
    
    # Process batch generation
    total_videos = max(1, args.batch)
    print(f"\n=======================================================")
    print(f"🎬 FLAG LINE BATTLE - VIDEO GENERATION PIPELINE")
    print(f"📦 Total Videos to Generate: {total_videos}")
    print(f"📁 Output Directory: {OUTPUT_DIR}")
    print(f"=======================================================\n")

    generated_files = []
    for idx in range(total_videos):
        if total_videos > 1:
            print(f"\n>>> [Video {idx + 1} of {total_videos}] <<<")
            
        # Determine countries
        if args.countries:
            raw_list = [c.strip() for c in args.countries.split(",") if c.strip()]
            valid_list = []
            for c in raw_list:
                # Case insensitive match
                match = next((k for k in all_countries if k.lower() == c.lower()), None)
                if match:
                    valid_list.append(match)
                else:
                    print(f"⚠️ Warning: Country '{c}' not found in database, skipping.")
            if len(valid_list) < 2:
                print("❌ Need at least 2 valid countries. Defaulting to random.")
                valid_list = random.sample(all_countries, 3)
            selected_countries = valid_list
        else:
            k = args.count if (args.count and args.count >= 2) else random.choice([3, 4])
            selected_countries = random.sample(all_countries, k)

        out_path = generate_battle_video(
            countries=selected_countries,
            total_lines=args.lines,
            intro_duration=args.intro,
            output_filename=args.out if total_videos == 1 else None
        )
        generated_files.append(out_path)

    print("\n🎉 ALL GENERATION TASKS COMPLETE!")
    print("Saved files:")
    for f in generated_files:
        print(f"  ⭐ {f}")
    print("\n👉 Upload directly to Facebook Reels, Facebook Pages, YouTube Shorts, or TikTok!\n")

if __name__ == "__main__":
    main()
