import os
import re
import json
import time
import uuid
import requests
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# --- CONFIGURATION ---
# Set to True for your initial local run today.
# Set to False before pushing to GitHub Actions for daily runs.
INITIAL_FULL_SCRAPE = True

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "@hamrobz_shutter")
STATE_FILE = "seen_listings.json"

SEARCH_URL = "https://hamrobazaar.com/api/products/search"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://hamrobazaar.com",
    "Referer": "https://hamrobazaar.com/"
}

EXCLUDED_CITIES = [
    "dharan", "biratnagar", "pokhara", "butwal", "chitwan", "narayangarh",
    "itahari", "jhapa", "damak", "birtamode", "nepalgunj", "dhangadhi",
    "hetauda", "birgunj", "janakpur", "bhairahawa", "surkhet"
]

def load_seen_ids():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_seen_ids(seen_set):
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(list(seen_set)), f, indent=2)

def make_slug(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "shutter-for-rent"

def get_image_url(item):
    img = item.get("imageUrl") or item.get("image") or item.get("thumbnailUrl")
    if not img and isinstance(item.get("images"), list) and item["images"]:
        first = item["images"][0]
        img = first.get("imageUrl") if isinstance(first, dict) else first
    if img and not img.startswith("http"):
        img = f"https://hamrobazaar.blr1.cdn.digitaloceanspaces.com/{img.lstrip('/')}"
    return img

def get_posted_date(item):
    """Extracts and formats the listing date."""
    raw_date = item.get("createdDate") or item.get("createdAt") or item.get("date")
    if raw_date:
        # Extracts YYYY-MM-DD from ISO timestamp strings
        return str(raw_date).split("T")[0]
    return "Recently"

def get_location_details(item):
    """Combines area and location description for precise place metadata."""
    loc_desc = item.get("locationDescription") or item.get("address") or ""
    area = item.get("areaName") or item.get("city") or ""
    
    if area and loc_desc and area.lower() not in loc_desc.lower():
        return f"{area}, {loc_desc}"
    return loc_desc or area or "Kathmandu"

def is_valid_kathmandu_rental(item):
    title = item.get("name", "")
    desc = item.get("description", "")
    loc = item.get("locationDescription", "") or item.get("address", "")
    full_text = f"{title} {desc} {loc}".lower()

    if any(city in full_text for city in EXCLUDED_CITIES):
        return False
    if "for sale" in title.lower() or "bikri" in title.lower():
        return False
    return True

def fetch_listings_from_source(payload_base, max_pages):
    collected_items = []
    page = 1

    while page <= max_pages:
        payload = payload_base.copy()
        payload["pageNumber"] = page

        try:
            response = requests.post(SEARCH_URL, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break

        listings = data.get("data", [])
        if not listings:
            break

        collected_items.extend(listings)
        if max_pages == 1:
            break

        page += 1
        time.sleep(0.5)

    return collected_items

def send_telegram_alert(caption, photo_url=None):
    if photo_url:
        tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": photo_url,
            "caption": caption,
            "parse_mode": "HTML"
        }
        while True:
            resp = requests.post(tg_url, json=payload, timeout=20)
            data = resp.json()
            if data.get("ok"):
                return data
            if data.get("error_code") == 429:
                retry_after = data.get("parameters", {}).get("retry_after", 10)
                print(f"Rate limited. Sleeping {retry_after}s...")
                time.sleep(retry_after + 1)
                continue
            break

    # Fallback to text-only send
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": caption,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    while True:
        resp = requests.post(tg_url, json=payload, timeout=15)
        data = resp.json()
        if data.get("ok"):
            return data
        if data.get("error_code") == 429:
            retry_after = data.get("parameters", {}).get("retry_after", 10)
            time.sleep(retry_after + 1)
            continue
        return data

def main():
    seen_ids = load_seen_ids()
    max_pages = 999 if INITIAL_FULL_SCRAPE else 1

    payload_keyword = {
        "pageNumber": 1, "pageSize": 30,
        "latitude": 27.7172, "longitude": 85.3240,
        "deviceId": str(uuid.uuid4()), "isHBSelect": False, "deviceSource": "web",
        "searchParams": {"searchValue": "shutter", "searchBy": "", "searchByDistance": 15000},
        "filterParams": {"condition": 0, "priceFrom": 0, "priceTo": 0, "isPriceNegotiable": None, "category": "", "categoryIds": "", "brand": "", "brandIds": "", "advanceFilter": ""},
        "sortParam": ""
    }

    payload_category = {
        "pageNumber": 1, "pageSize": 30,
        "latitude": 27.7172, "longitude": 85.3240,
        "deviceId": str(uuid.uuid4()), "isHBSelect": False, "deviceSource": "web",
        "searchParams": {"searchValue": "", "searchBy": "", "searchByDistance": 15000},
        "filterParams": {"condition": 0, "priceFrom": 0, "priceTo": 0, "isPriceNegotiable": None, "category": "A9C70559-16C7-49D8-988B-9AC3C9F975E7", "categoryIds": "", "brand": "", "brandIds": "", "advanceFilter": ""},
        "sortParam": ""
    }

    print("Fetching listings from Keyword Search and Category Browse...")
    items_keyword = fetch_listings_from_source(payload_keyword, max_pages)
    items_category = fetch_listings_from_source(payload_category, max_pages)

    unique_items_map = {}
    for item in items_keyword + items_category:
        item_id = str(item.get("id"))
        if item_id:
            unique_items_map[item_id] = item

    all_listings = list(unique_items_map.values())
    print(f"Total unique listings gathered: {len(all_listings)}")

    new_listings_found = 0

    for item in all_listings:
        item_id = str(item.get("id"))
        if item_id in seen_ids:
            continue

        if not is_valid_kathmandu_rental(item):
            seen_ids.add(item_id)
            continue

        title = item.get("name", "Shutter for Rent").strip()
        price = item.get("price", "N/A")
        location = get_location_details(item)
        posted_date = get_posted_date(item)
        photo_url = get_image_url(item)
        slug = make_slug(title)
        listing_url = f"https://hamrobazaar.com/detail/for-rent-shutter-shop-space/{slug}/{item_id}"

        price_str = f"Rs. {price:,}" if isinstance(price, (int, float)) else f"Rs. {price}"
        
        # Enhanced caption layout including Location and Posted Date metadata
        caption = (
            f"🏢 <b>{title}</b>\n"
            f"💰 <b>Rent:</b> {price_str}\n"
            f"📍 <b>Location:</b> {location}\n"
            f"📅 <b>Posted:</b> {posted_date}\n\n"
            f"👉 <a href=\"{listing_url}\">Open Listing on Hamro Bazaar</a>"
        )

        print(f"Sending alert for: {title} | Date: {posted_date} | Photo: {bool(photo_url)}")
        res = send_telegram_alert(caption, photo_url)

        if res.get("ok"):
            seen_ids.add(item_id)
            new_listings_found += 1
            save_seen_ids(seen_ids)
            time.sleep(3.2)  # Respect Telegram rate limit
        else:
            print(f"Failed to send alert: {res}")

    save_seen_ids(seen_ids)
    print(f"Finished. Sent {new_listings_found} new alerts. Total tracked IDs: {len(seen_ids)}.")

if __name__ == "__main__":
    main()