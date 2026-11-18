import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://wasalt.sa"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

SEEDS = [
    "/en/apartments-for-sale-in-jeddah",
    "/en/villas-for-sale-in-riyadh",
    "/en/apartments-for-rent-in-riyadh",
    "/en/apartments-for-rent-in-jeddah",
]
PAGES_PER_SEED = 2        # 30 listings per page -> up to ~60 per category
MAX_LISTINGS = 240


def find_listings(html):
    """From a listing page, return the set of property URLs on it."""
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        full = urljoin(BASE, a["href"]).split("?")[0]
        if "/en/property/" in full:
            links.add(full)
    return links


def to_number(value):
    """Turn '118.71', 630000 or '' into a number or None."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_listing(url, html):
    """Read one property's facts from the page's __NEXT_DATA__ JSON."""
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("script", id="__NEXT_DATA__")
    if not tag:
        return None
    details = json.loads(tag.string)["props"]["pageProps"].get("propertyDetailsV3")
    if not details:
        return None

    info = details["propertyInfo"]
    attrs = {a["key"]: a["value"] for a in details.get("attributes", [])}

    # The description is stored as HTML (<p>...</p>), so strip the tags
    description = BeautifulSoup(info.get("description") or "", "html.parser").get_text("\n", strip=True)

    is_rent = info.get("propertyFor") == "rent"
    return {
        "source": "Wasalt",
        "url": url,
        "title": info.get("title", ""),
        "purpose": info.get("propertyFor", ""),
        "property_type": info.get("propertySubType", ""),
        "city": info.get("city", ""),
        "district": info.get("district", ""),
        "address": info.get("address", ""),
        "price_sar": to_number(info.get("expectedRent") if is_rent else info.get("salePrice")),
        "rent_frequency": info.get("rentFreq") or None,
        "bedrooms": to_number(attrs.get("noOfBedrooms")),
        "built_up_area_sqm": to_number(attrs.get("builtUpArea")),
        "description": description,
    }


def fetch(url, tries=3):
    """Download a page, retrying slow or failed requests. Returns HTML or None."""
    for attempt in range(1, tries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=40)
            if r.status_code == 200:
                return r.text
            print("  status", r.status_code, "for", url)
        except requests.RequestException as e:
            print(f"  attempt {attempt} failed ({e.__class__.__name__}), retrying")
        time.sleep(5 * attempt)          # wait 5s, then 10s, then 15s
    return None


# Step 1: collect listing URLs from each category page
all_urls = {}             # a dict keeps insertion order and ignores duplicates
for seed in SEEDS:
    for page in range(1, PAGES_PER_SEED + 1):
        page_url = BASE + seed + (f"?page={page}" if page > 1 else "")
        html = fetch(page_url)
        if not html:
            print("Skipping", page_url)
            break
        found = find_listings(html)
        print(seed, "page", page, "->", len(found), "listings")
        for u in found:
            all_urls[u] = True
        time.sleep(2)

urls = list(all_urls)[:MAX_LISTINGS]
print("Total unique listings to fetch:", len(urls))

# Step 2: visit each listing and extract its facts
results = []
for i, url in enumerate(urls, 1):
    try:
        html = fetch(url)
        listing = extract_listing(url, html) if html else None
    except Exception as e:
        print(i, "FAILED", url, e)
        continue
    if listing:
        results.append(listing)
    if i % 20 == 0:
        print(f"{i}/{len(urls)} done")
    time.sleep(2)

with open("wasalt.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("Saved", len(results), "listings to wasalt.json")