import json
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
}
url = "https://wasalt.sa/en/property/sale/apartment-11871-sqm-with-3-bedrooms-5970587"

resp = requests.get(url, headers=HEADERS, timeout=20)
soup = BeautifulSoup(resp.text, "html.parser")
tag = soup.find("script", id="__NEXT_DATA__")
print("Found __NEXT_DATA__:", tag is not None)

data = json.loads(tag.string)
with open("listing_sample.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)


def find_paths(obj, target, path="data"):
    """Print the path to every value that contains `target`."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            find_paths(value, target, f"{path}[{key!r}]")
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            find_paths(value, target, f"{path}[{i}]")
    elif target.lower() in str(obj).lower():
        print(path, "=", str(obj)[:80])


details = data["props"]["pageProps"]["propertyDetailsV3"]

print("--- propertyInfo keys ---")
for key, value in details["propertyInfo"].items():
    print(key, "=", str(value)[:60])

print("\n--- attributes ---")
for item in details["attributes"]:
    print(item)