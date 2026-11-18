# Property Assistant: DarGlobal & Wasalt chatbot

**Live demo:** https://property-chatbot-njur.onrender.com/
(Hosted on Render's free tier: the first request after 15 minutes idle takes about a minute to wake up.)

Ask about DarGlobal's luxury projects (UAE, Saudi Arabia, Oman, Qatar, Spain, UK) and Wasalt
apartments/villas for sale and rent in Riyadh and Jeddah, in English or Arabic.

## How it works
1. **Scraping** (run locally, results saved as JSON)
   - `scrape_darglobal.py`: 38 projects. The site is behind Incapsula bot protection, so I used
     Playwright to drive a real browser. Some newer pages are rendered by JavaScript, so the
     scraper waits and re-reads pages that come back nearly empty.
   - `scrape_wasalt.py`: 95 listings. Instead of parsing page text, it reads the structured
     `__NEXT_DATA__` JSON that Next.js embeds in each page, which gives clean fields (price,
     bedrooms, district) regardless of the description's language. Only the property fields
     needed are kept; advertiser names and contact details are never stored.
   - Both scrapers send requests a few seconds apart and retry failed requests with backoff.
2. **Retrieval** (`search.py`): structured filters taken from the question (sale/rent, city,
   bedrooms) narrow the candidates, then BM25 keyword ranking picks the top 5.
3. **Generation** (`ask.py`): the top 5 documents go to a free OpenRouter model with a system
   prompt that restricts answers to the provided data and requires a source link. If a model
   is rate-limited, the next one in a fallback list is tried.
4. **App** (`main.py`, `index.html`): FastAPI serves a chat page and a `/chat` endpoint.
   Containerised with Docker and deployed on Render; the API key is an environment variable.

## Run locally
    pip install -r requirements.txt
    export OPENROUTER_API_KEY=your-key
    python -m uvicorn main:app --port 7860

## Design decisions
- **Filters + BM25 instead of embeddings:** users state hard requirements (rent, city, number
  of bedrooms) that keyword or vector similarity handles poorly; filtering first makes them exact.
- **Scrape offline, serve a snapshot:** keeps the app fast and avoids hitting the sites per question.

## Limitations
- Data is a snapshot from 18 Nov 2026; prices and availability may have changed.
- Wasalt coverage is partial: pagination returned duplicate pages, and some rental listings
  were removed between crawling and fetching (404).
- Some source listings contain implausible values (e.g. very large areas); the bot reports them as listed.
- No conversation memory: each question is answered independently.
- Free models are shared and sometimes rate-limited, so answer speed and quality vary.