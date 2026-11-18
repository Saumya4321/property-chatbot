import json
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

BASE = "https://darglobal.co.uk"
SKIP = {"/", "/one-of-one", "/investor", "/blog", "/press", "/pay-online", "/get-in-touch",
        "/why-invest", "/privacy-policy", "/terms-of-uses", "/terms-conditions", "/faq", "/insights"}
NAME_FIXES = {
    BASE + "/rayana/trump-mansions": "Trump Mansions",
    BASE + "/amaya/amaya-plots": "Amaya Plots",
}

def find_projects(html):
    """From the /projects page, return {project_url: (card_title, location)}."""
    soup = BeautifulSoup(html, "html.parser")
    projects = {}
    for a in soup.find_all("a", href=True, title=True):
        url = urljoin(BASE, a["href"])
        path = urlparse(url).path.rstrip("/") or "/"
        if not url.startswith(BASE) or path in SKIP or path.startswith("/projects"):
            continue
        # The card's visible text holds the name and a location like "Dubai, UAE"
        parts = [s for s in a.stripped_strings if s != a["title"]]
        location = next((s for s in parts if "," in s), "")
        projects[url] = (a["title"], location)
    return projects


def extract(html):
    """From a project page, return its heading, meta description and readable text."""
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    title = h1.get_text(" ", strip=True) if h1 else ""
    meta = soup.find("meta", attrs={"name": "description"})
    description = meta["content"] if meta and meta.get("content") else ""

    # Remove things that aren't content: code, menus, forms
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form"]):
        tag.decompose()
    lines = [line.strip() for line in soup.get_text("\n").splitlines()]
    STOP_AT = ("other projects", "register your interest")
    JUNK = {"download brochure", "book unit", "gallery", "view all images",
            "show more", "choose your residence"}

    cleaned = []
    for line in lines:
        low = line.lower()
        if low.startswith(STOP_AT):   # everything after this is cross-links or forms
            break
        if len(line) > 1 and low not in JUNK:
            cleaned.append(line)
    lines = list(dict.fromkeys(cleaned))      # drop repeated lines, keep order
    return title, description, "\n".join(lines)


results = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, channel="msedge")
    page = browser.new_page()
    page.goto(BASE + "/projects", wait_until="networkidle")   # passes the bot check once
    projects = find_projects(page.content())
    print("Found", len(projects), "projects")

    for i, (url, (card_title, location)) in enumerate(list(projects.items()), 1):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            title, description, text = extract(page.content())
            if len(text) < 300:               # probably built by JavaScript: give it time
                page.wait_for_timeout(6000)
                title, description, text = extract(page.content())
        except Exception as e:
            print(i, "FAILED", url, e)
            continue
        results.append({
            "source": "DarGlobal",
            "url": url,
            "name": NAME_FIXES.get(url, card_title),
            "location": location,
            "description": description,
            "text": text[:8000],
        })
        print(i, NAME_FIXES.get(url, card_title), "|", location, "|", len(text), "chars")
        time.sleep(2)                    # be polite: one page every ~2 seconds
    browser.close()

with open("darglobal.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("Saved", len(results), "projects to darglobal.json")