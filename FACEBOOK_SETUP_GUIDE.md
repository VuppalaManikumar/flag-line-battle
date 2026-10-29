# 📘 Facebook Page Auto-Posting Setup Guide

This guide walks you through connecting your Facebook Page so that [`auto_post_to_facebook.bat`](file:///C:/Users/manik/.gemini/antigravity/scratch/flag-line-battle/auto_post_to_facebook.bat) can automatically generate and publish **3 Facebook Reels per day** on complete autopilot.

---

## ⚙️ Step 1: Find Your Facebook Page ID

1. Open your Facebook Page in your browser.
2. Click on the **About** tab (or **Settings** $\to$ **Page setup**).
3. Scroll to the bottom to find your **Page ID** (a 15–16 digit number like `105294829103948`).
4. Copy this number.

---

## 🔑 Step 2: Get Your Facebook Page Access Token

To upload videos via Facebook's API, Meta provides a **Page Access Token**:

1. Go to the **[Meta Graph API Explorer](https://developers.facebook.com/tools/explorer/)**.
2. Log in with the Facebook account that owns/manages your Page.
3. In the right-hand panel:
   * **Meta App**: Select your app (if you don't have one, click *Create App* $\to$ choose *Other* $\to$ *Business*).
   * **User or Page**: Click the dropdown and select **your Facebook Page**.
   * **Add Permissions**: Click *Add a Permission* and check:
     * `pages_manage_posts`
     * `pages_read_engagement`
     * `pages_show_list`
4. Click **Generate Access Token**.
5. Approve the popup permissions for your page.
6. Copy the generated Access Token!

> [!TIP]
> **To make your token never expire**:
> 1. Go to [developers.facebook.com/tools/debug/accesstoken](https://developers.facebook.com/tools/debug/accesstoken/).
> 2. Paste your token and click **Debug**.
> 3. Click **Extend Access Token** at the bottom to convert it into a permanent long-lived token!

---

## 📝 Step 3: Connect Your Page in 1 Click

You can connect your page in two easy ways:

### Option A: Using the Quick Connect Wizard (Easiest)
Double-click [`connect_facebook.bat`](file:///C:/Users/manik/.gemini/antigravity/scratch/flag-line-battle/connect_facebook.bat).
Paste your Page ID and Page Access Token when prompted. It will verify the connection and save your settings automatically!

### Option B: Paste Directly into `facebook_config.json`
Open [`facebook_config.json`](file:///C:/Users/manik/.gemini/antigravity/scratch/flag-line-battle/facebook_config.json) in your project folder:

```json
{
  "facebook_page_id": "PASTE_YOUR_PAGE_ID_HERE",
  "facebook_page_access_token": "PASTE_YOUR_PAGE_ACCESS_TOKEN_HERE",
  "videos_per_day": 3,
  "post_as_reels": true,
  "auto_schedule": true,
  "schedule_target_hours": [10, 15, 20]
}
```

---

## 🚀 Step 4: Schedule All 7 Days (21 Videos) with 1 Click!

Just **double-click [`schedule_7_days.bat`](file:///C:/Users/manik/.gemini/antigravity/scratch/flag-line-battle/schedule_7_days.bat)**!

Every time you run this:
1. It generates **21 unique Flag Battle videos** with randomized countries, physics, and the selection roulette intro.
2. Formats viral titles, matchups with country emojis, comment hooks, and trending hashtags.
3. Automatically schedules **3 Reels for every day across the next 7 days** on your Facebook Page:
   - **Slot 1 (Morning)**: 10:00 AM
   - **Slot 2 (Afternoon)**: 3:00 PM
   - **Slot 3 (Evening)**: 8:00 PM
4. Saves a full publishing schedule manifest in `output/7_day_schedule_manifest.txt`.

---

## 📅 Daily 1-Day Posting (Alternative)

If you only want to generate and schedule **today's 3 videos**, double-click:  
[`auto_post_to_facebook.bat`](file:///C:/Users/manik/.gemini/antigravity/scratch/flag-line-battle/auto_post_to_facebook.bat)

---

## 🤖 (Optional) 100% Hands-Free Daily Schedule

If you don't even want to click the `.bat` file every day, double-click:
[`setup_daily_schedule.bat`](file:///C:/Users/manik/.gemini/antigravity/scratch/flag-line-battle/setup_daily_schedule.bat)

This will create a Windows Task Scheduler job that runs `auto_post_to_facebook.bat` automatically **every morning at 8:00 AM** in the background!
