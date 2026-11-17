# 🏢 Hamro Bazaar Kathmandu Shutter & Shop Rental Bot

An automated, lightweight Python scraper that monitors [Hamro Bazaar](https://hamrobazaar.com/) for real-time "Shutter & Shop Space for Rent" listings within the **Kathmandu Valley**, filtering out unwanted regions and instantly dispatching rich photo alerts directly to a Telegram channel.

---

## ✨ Key Features

- **Dual-Source Discovery:** Fetches and merges results from both keyword search (`"shutter"`) and Hamro Bazaar's exact category endpoint (`For Rent - Shutter & Shop Space`) to ensure zero missed listings.
- **Strict Kathmandu Valley Filtering:** Automatically filters out listings outside Kathmandu (such as Dharan, Pokhara, Butwal, etc.) using both API coordinate mapping (`15` km radius from Kathmandu center) and text-based keyword exclusions.
- **Rich Visual Alerts (`sendPhoto`):** Sends individual photo previews of the properties with clean fallbacks for listings without images.
- **Detailed Metadata:** Each alert includes the exact listing title, monthly rent price, precise location/area description, publication date, and a direct deep-link (`/detail/for-rent-shutter-shop-space/{slug}/{id}`) to the listing.
- **Smart Deduplication:** Utilizes a persistent local state file (`seen_listings.json`) to guarantee zero duplicate alerts.
- **Automated Daily Runs:** Fully configured for serverless execution via GitHub Actions (`cron` schedule), complete with automated state commits.

---

## 🛠️ Tech Stack

- **Language:** Python 3.11+
- **HTTP Client:** `requests`
- **Environment Management:** `python-dotenv`
- **Notifications:** Telegram Bot API (`sendPhoto` / `sendMessage`)
- **Automation:** GitHub Actions (Cron Scheduler)

---

## 🚀 Local Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/hamrobazar-shutter-scraper.git
cd hamrobazar-shutter-scraper
```

### 2. Install Dependencies
```bash
pip install requests python-dotenv
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory of your project:
```env
TELEGRAM_BOT_TOKEN=your_bot_father_token_here
TELEGRAM_CHAT_ID=@your_channel_username
```

### 4. Run the Initial Seed Scrape
To populate your channel with existing listings and initialize your `seen_listings.json` file:
1. Open `scraper.py` and ensure `INITIAL_FULL_SCRAPE = True`.
2. Run the script:
   ```bash
   python scraper.py
   ```

---

## 🤖 GitHub Actions Automation (Daily Cron Job)

To run this scraper automatically every day without keeping a local server running:

1. **Update Code for Daily Mode:** Open `scraper.py` and set `INITIAL_FULL_SCRAPE = False` so it only checks the newest page during automated runs.
2. **Push Code to GitHub:**
   ```bash
   git add .
   git commit -m "Configure daily scraper"
   git push origin main
   ```
3. **Add Repository Secrets:**
   - Go to your GitHub repository **Settings $\rightarrow$ Secrets and variables $\rightarrow$ Actions**.
   - Click **New repository secret**.
   - Name: `TELEGRAM_BOT_TOKEN` | Value: *Your Telegram Bot Token*
4. **Verify Workflow:** The workflow file located at `.github/workflows/daily_scrape.yml` will automatically execute every day at **03:15 UTC (09:00 AM Nepal Time)**, post any new shutter listings to your Telegram channel, and update your `seen_listings.json` state automatically.

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).