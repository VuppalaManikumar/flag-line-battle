# ⚔️ Flag Line Battle - 100% Automated Facebook Reels Bot (10 Reels/Day)

Automated physics simulation and high-definition video generator for viral **Country Flag Line Battles**, fully automated with **GitHub Actions cloud autopilot** to generate and post **10+ Facebook Reels every single day** without human interaction!

Inspired by popular simulation channels like `@d_studio_Loops`, this system creates oddly satisfying, high-engagement vertical videos where world flags battle inside a neon circular arena until only one flag survives!

---

## 🌟 Key Features

* 🤖 **100% Cloud Autopilot (Zero Human Intervention)**:
  * Runs via GitHub Actions cron workflows directly in GitHub's cloud.
  * Your local computer does NOT need to stay on.
  * Automatically generates, titles, tags, and schedules **10 Facebook Reels daily** to Meta's servers.
* 🕒 **10 Optimized Peak Viral Slots**:
  * Posts spaced every ~1.5 hours across peak viewer engagement times:
    `08:00`, `09:30`, `11:00`, `12:30`, `14:00`, `15:30`, `17:00`, `18:30`, `20:00`, `21:30`
  * Fully customizable timezone (defaults to `Asia/Kolkata` / IST).
* 🎲 **Country Roulette Intro**:
  * 4.8s spinning flag picker roulette with sound effects before the battle begins.
* 📏 **"How Many Touch = That Many Cut" Multi-Line Physics**:
  * 30 starting lines tethered to arena wall.
  * Touching the outer circular ring spawns new tethered lines.
  * Opponent flags slicing across lines cut every single line contacted instantly.
* 🎬 **1080x1920 60 FPS Vertical HD**:
  * Crystal-clear MP4 with synced SFX (laser cuts, bounces, explosions, royal fanfare) and synthesized bass rhythm.
* ✍️ **Dynamic Viral Captions & Tags**:
  * Country match badges, emojis, call-to-actions ("Drop your country!"), winner callouts, and trending hashtags.

---

## ⚙️ GitHub Automation Setup (Already Connected!)

Your repository is connected at:
👉 **[https://github.com/VuppalaManikumar/flag-line-battle](https://github.com/VuppalaManikumar/flag-line-battle)**

### Stored GitHub Secrets:
The following secrets are already encrypted and configured in your GitHub repository:
* `FB_PAGE_ID`: Your verified Facebook Page ID (`1405394435990645`)
* `FB_PAGE_ACCESS_TOKEN`: Your verified Facebook Page Token (with `pages_manage_posts` & `publish_video`)
* `VIDEOS_PER_DAY`: `10`
* `SCHEDULE_TIMEZONE`: `Asia/Kolkata`

### Workflow Schedule:
* File: [`.github/workflows/daily_reels.yml`](.github/workflows/daily_reels.yml)
* Automated Cron: `0 2 * * *` (02:00 UTC = 07:30 AM IST every day).
* Manual Trigger: Go to **Actions** tab on GitHub $\to$ **Daily 10x Facebook Reels Autopilot** $\to$ click **Run workflow**.

---

## 💻 Local Usage

You can also run everything locally anytime:

### 1. Daily 10 Reels Local Batch
Double-click [`auto_post_to_facebook.bat`](auto_post_to_facebook.bat) or run:
```bash
python fb_auto_poster.py --count 10
```

### 2. 7-Day Advance Scheduler (70 or 21 Reels)
Double-click [`schedule_7_days.bat`](schedule_7_days.bat) or run:
```bash
python schedule_7_days.py
```

### 3. Interactive Browser Studio
```bash
python web_app.py
```
Open **[http://localhost:5000](http://localhost:5000)** to watch battles live and export customized videos.

---

## 📁 Project Structure

```
flag-line-battle/
├── .github/workflows/
│   └── daily_reels.yml           # GitHub Actions 10x/day automation workflow
├── assets/
│   ├── flags/                    # Preloaded circular flag textures
│   └── sounds/                   # Procedural audio effects (.wav)
├── countries.py                  # 30+ Country database, laser colors & flags
├── simulator.py                  # Multi-line physics simulation & cutting engine
├── renderer.py                   # 1080x1920 60FPS Pygame canvas & intro roulette
├── sound_gen.py                  # Sound synthesizer for sfx & bass rhythm
├── video_builder.py              # FFmpeg video muxer + audio mixing pipeline
├── fb_uploader.py                # Official Meta 3-phase Reels API uploader & scheduler
├── fb_auto_poster.py             # 10x daily batch generator & cloud poster
├── schedule_7_days.py            # Multi-day batch scheduling utility
├── auto_post_to_facebook.bat     # 1-click batch runner (10 Reels/day)
├── requirements.txt              # Python dependencies
└── README.md
```
