"""
scraper.py — Real-time Snapdeal product & review scraper
Uses Selenium for JavaScript-rendered review pages.

SETUP (one time):
    pip install selenium webdriver-manager

ChromeDriver is auto-managed by webdriver-manager.
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import hashlib
import json
import time
import random
from datetime import datetime, timedelta

CACHE_DB           = "cache.db"
CACHE_EXPIRY_HOURS = 24

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) "
    "Gecko/20100101 Firefox/121.0",
]

def _get_headers() -> dict:
    return {
        "User-Agent":      random.choice(USER_AGENTS),
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection":      "keep-alive",
        "DNT":             "1",
    }


# ── SQLite cache ──────────────────────────────────────────────────────────────

def _init_cache():
    conn = sqlite3.connect(CACHE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS query_cache (
            query_hash TEXT PRIMARY KEY,
            query      TEXT,
            results    TEXT,
            cached_at  TEXT
        )
    """)
    conn.commit()
    conn.close()


def _get_cached(query: str):
    _init_cache()
    key  = hashlib.md5(query.lower().strip().encode()).hexdigest()
    conn = sqlite3.connect(CACHE_DB)
    row  = conn.execute(
        "SELECT results, cached_at FROM query_cache WHERE query_hash=?", (key,)
    ).fetchone()
    conn.close()
    if row:
        cached_at = datetime.fromisoformat(row[1])
        if datetime.now() - cached_at < timedelta(hours=CACHE_EXPIRY_HOURS):
            print(f"[Cache] Returning cached results for '{query}'")
            return json.loads(row[0])
    return None


def _set_cache(query: str, results: list):
    _init_cache()
    key  = hashlib.md5(query.lower().strip().encode()).hexdigest()
    conn = sqlite3.connect(CACHE_DB)
    conn.execute(
        "INSERT OR REPLACE INTO query_cache (query_hash, query, results, cached_at) "
        "VALUES (?,?,?,?)",
        (key, query, json.dumps(results), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


# ── Selenium driver setup ─────────────────────────────────────────────────────

def _get_selenium_driver():
    """
    Create a headless Chrome Selenium driver.
    webdriver-manager auto-downloads the correct ChromeDriver.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")

    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


# ── Snapdeal search scraper (requests — fast) ─────────────────────────────────

def _parse_product_card(card) -> dict | None:
    name_tag = (
        card.select_one("p.product-title")        or
        card.select_one("div.product-title")      or
        card.select_one("p.product-desc-name")
    )
    price_tag = (
        card.select_one("span.product-price")     or
        card.select_one("div.product-price")      or
        card.select_one("span.lfloat.product-price")
    )
    rating_tag = (
        card.select_one("div.filled-stars")       or
        card.select_one("span.product-rating")
    )
    review_tag = (
        card.select_one("p.product-rating-count") or
        card.select_one("span.rating-count")
    )
    link_tag = card.select_one("a[href]")

    if not name_tag or not price_tag:
        return None

    name  = name_tag.get_text(strip=True)
    price = price_tag.get_text(strip=True)

    rating = "N/A"
    if rating_tag:
        style = rating_tag.get("style", "")
        if "width" in style:
            try:
                pct    = float(style.split("width:")[1].replace("%","").replace(";","").strip())
                rating = str(round(pct / 20, 1))
            except Exception:
                rating = rating_tag.get_text(strip=True) or "N/A"
        else:
            rating = rating_tag.get_text(strip=True) or "N/A"

    review_count = review_tag.get_text(strip=True) if review_tag else ""

    url = ""
    if link_tag:
        href = link_tag.get("href", "")
        url  = href if href.startswith("http") else "https://www.snapdeal.com" + href

    return {
        "name":         name,
        "price":        price,
        "rating":       rating,
        "review_count": review_count,
        "reviews":      [],
        "url":          url,
    }


def scrape_search(query: str, max_results: int = 10) -> list[dict]:
    url = (
        f"https://www.snapdeal.com/search?"
        f"keyword={query.replace(' ', '%20')}&sort=rlvncy"
    )
    print(f"[Scraper] Fetching search: {url}")
    try:
        resp = requests.get(url, headers=_get_headers(), timeout=12)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[Scraper] Search request failed: {e}")
        return []

    soup  = BeautifulSoup(resp.text, "html.parser")
    cards = (
        soup.select("div.product-tuple-listing") or
        soup.select("div.col-sd-12.product-tuple") or
        soup.select("div.product-desc-rating")
    )

    ACCESSORY_KEYWORDS = [
        "stand","holder","mount","selfie stick","tripod",
        "charger","cable","wire","cord","adapter","hub","dock",
        "cover","case","back cover","flip cover","pouch","sleeve",
        "tempered glass","screen guard","screen protector","protector",
        "strap","skin","wallet","bag","aux","flash light","power bank",
    ]
    MAIN_PRODUCT_KEYWORDS = [
        "mobile","smartphone","phone","laptop","tablet","ipad",
        "watch","smartwatch","camera","television","tv","monitor",
        "refrigerator","fridge","washing machine","microwave",
        "fan","cooler","iron","trimmer","printer","router",
    ]

    query_lower            = query.lower()
    is_main_product_search = any(kw in query_lower for kw in MAIN_PRODUCT_KEYWORDS)
    is_accessory_search    = any(kw in query_lower for kw in ACCESSORY_KEYWORDS)

    def is_relevant(name: str) -> bool:
        name_lower = name.lower()
        if is_accessory_search:
            return True
        if is_main_product_search:
            for acc in ACCESSORY_KEYWORDS:
                if name_lower.startswith(acc):
                    return False
                words       = name_lower.split()
                first_three = " ".join(words[:3])
                if acc in first_three and acc not in query_lower:
                    return False
        return True

    products = []
    for card in cards:
        parsed = _parse_product_card(card)
        if parsed and is_relevant(parsed["name"]):
            products.append(parsed)
        if len(products) >= max_results:
            break

    if not products:
        print("[Scraper] No products found. Snapdeal HTML may have changed.")
    return products


# ── Selenium review scraper ───────────────────────────────────────────────────

def scrape_reviews_selenium(product_url: str, max_reviews: int = 10) -> list[str]:
    """
    Scrape reviews using Selenium — handles JavaScript-rendered content.
    Opens a headless Chrome browser, waits for JS to load, extracts reviews.
    """
    if not product_url:
        return []

    print(f"[Selenium] Loading: {product_url[:70]}...")
    driver  = None
    reviews = []

    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        driver = _get_selenium_driver()
        driver.get(product_url)

        # Wait for body to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)

        # Scroll to trigger lazy-loaded reviews
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(1.5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)

        page_html = driver.page_source
        soup      = BeautifulSoup(page_html, "html.parser")

        # ── Strategy 1: targeted review selectors ────────────────────────────
        review_selectors = [
            "div.user-review p",
            "p.review-description",
            "div.review-description p",
            "span.review-description",
            "div.review-text",
            "p.review-text",
            "div.reviewTextDiv",
            "div[class*='review'] p",
            "div[class*='Review'] p",
            "p[class*='review']",
            "div[class*='userReview']",
            "div[class*='user-review']",
            "div[class*='reviewContent'] p",
            "div[class*='review-content'] p",
        ]
        for sel in review_selectors:
            tags = soup.select(sel)
            for tag in tags:
                text = tag.get_text(strip=True)
                if text and len(text) > 20 and text not in reviews:
                    reviews.append(text)
                if len(reviews) >= max_reviews:
                    break
            if reviews:
                print(f"[Selenium] Found {len(reviews)} reviews via: {sel}")
                break

        # ── Strategy 2: fallback <p> scan ────────────────────────────────────
        if not reviews:
            print("[Selenium] Fallback: scanning <p> tags...")
            skip_phrases = [
                "privacy policy","terms","home","cart","login","sign in",
                "wishlist","snapdeal","shop by","contact us",
                "rs.","₹","free delivery","cash on delivery",
            ]
            for p_tag in soup.find_all("p"):
                text = p_tag.get_text(strip=True)
                if (25 < len(text) < 600
                        and not any(s in text.lower() for s in skip_phrases)
                        and text not in reviews):
                    reviews.append(text)
                if len(reviews) >= max_reviews:
                    break

        # ── Strategy 3: Selenium direct element search ────────────────────────
        if not reviews:
            print("[Selenium] Fallback: direct element search...")
            skip_phrases = ["privacy","terms","login","cart","wishlist"]
            for css in ["p", "span"]:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, css)
                    for el in elements:
                        text = el.text.strip()
                        if (25 < len(text) < 500
                                and text not in reviews
                                and not any(s in text.lower() for s in skip_phrases)):
                            reviews.append(text)
                        if len(reviews) >= max_reviews:
                            break
                    if reviews:
                        print(f"[Selenium] Found {len(reviews)} via <{css}>")
                        break
                except Exception:
                    pass

    except ImportError:
        print("[Selenium] Not installed! Run: pip install selenium webdriver-manager")

    except Exception as e:
        print(f"[Selenium] Error: {e}")

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

    if not reviews:
        print(f"[Selenium] No reviews found for: {product_url[:60]}")
    else:
        print(f"[Selenium] Fetched {len(reviews)} reviews")

    return reviews[:max_reviews]


# ── Check if Selenium is available ───────────────────────────────────────────

def _selenium_available() -> bool:
    try:
        import selenium                                  # noqa
        from webdriver_manager.chrome import ChromeDriverManager  # noqa
        return True
    except ImportError:
        return False


# ── Main public function ──────────────────────────────────────────────────────

def scrape_snapdeal(
    query:         str,
    max_results:   int  = 10,
    use_cache:     bool = True,
    fetch_reviews: bool = True,
) -> list[dict]:
    """
    Full pipeline:
    1. Check 24h SQLite cache
    2. Scrape Snapdeal search results  (fast — requests)
    3. For each product scrape reviews (Selenium — JS-rendered)
    4. Cache and return
    """
    if use_cache:
        cached = _get_cached(query)
        if cached:
            return cached[:max_results]

    products = scrape_search(query, max_results=max_results)

    if fetch_reviews:
        use_sel = _selenium_available()
        if use_sel:
            print("[Scraper] Selenium ready — using JS-rendered review scraping")
        else:
            print("[Scraper] Selenium not found. Run:")
            print("  pip install selenium webdriver-manager")

        for i, p in enumerate(products):
            if p.get("url") and use_sel:
                p["reviews"] = scrape_reviews_selenium(p["url"], max_reviews=8)
            else:
                p["reviews"] = []
            if i < len(products) - 1:
                time.sleep(random.uniform(1.5, 2.5))

    if use_cache and products:
        _set_cache(query, products)

    return products


# ── Standalone test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = scrape_snapdeal("wireless headphones", max_results=2, fetch_reviews=True)
    for i, p in enumerate(results, 1):
        print(f"\n{'='*60}")
        print(f"#{i} {p['name']}")
        print(f"   Price  : {p['price']}")
        print(f"   Rating : {p['rating']}")
        print(f"   Reviews: {len(p['reviews'])} fetched")
        for r in p["reviews"][:3]:
            print(f"   > {r[:100]}")