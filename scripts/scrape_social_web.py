from __future__ import annotations

import argparse
import html
import json
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs, quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


SHONA_WORDS = {
    "ndiri", "ndinoda", "vanhu", "kuti", "uye", "zvino", "asi",
    "pane", "zvinhu", "mwana", "amai", "baba", "mhoro", "makadii",
    "zvakanaka", "ndatenda", "mwari", "nyika", "zimbabwe", "musha",
    "kubva", "kuenda", "kuuya", "vana", "munhu", "chii", "here",
    "nhai", "zviripo", "tichaona", "maita", "shamwari", "hama",
    "mufaro", "kutenda", "kuimba", "kurima", "kushanda", "kufara",
}

ROOT = Path(".")
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
STATE_FILE = ROOT / "STATE.json"
MANIFEST_FILE = RAW_DIR / "manifest.json"
ALL_CLEAN_FILE = PROCESSED_DIR / "all_clean.txt"
TRAIN_FILE = PROCESSED_DIR / "train.txt"
VALID_FILE = PROCESSED_DIR / "valid.txt"
TEST_FILE = PROCESSED_DIR / "test.txt"
STATS_FILE = PROCESSED_DIR / "stats.json"

DEFAULT_LOG_FILE = Path("logs") / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_agent17.log"


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9,sn;q=0.8",
        }
    )
    return session


def write_log(log_file: Path, level: str, phase: str, message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{level}] [{phase}] {message}"
    print(entry)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as handle:
        handle.write(entry + "\n")


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return default


def save_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def normalize_text(text: str) -> str:
    text = html.unescape(text or "")
    text = text.replace("\xa0", " ")
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" \t\r\n\"'“”‘’•-*|")


def text_blocks(text: str) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []
    blocks: list[str] = []
    for chunk in re.split(r"(?:\r?\n)+", normalized):
        chunk = normalize_text(chunk)
        if not chunk:
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", chunk):
            sentence = normalize_text(sentence)
            if sentence:
                blocks.append(sentence)
    return blocks


def non_alpha_ratio(text: str) -> float:
    chars = [ch for ch in text if not ch.isspace()]
    if not chars:
        return 1.0
    non_alpha = sum(1 for ch in chars if not ch.isalpha())
    return non_alpha / len(chars)


def is_shona(text: str) -> bool:
    words = re.findall(r"[a-z]+", text.lower())
    if len(words) < 3:
        return False
    shona_count = sum(1 for word in words if word in SHONA_WORDS)
    return shona_count / len(words) >= 0.15


def clean_line(text: str) -> str | None:
    text = normalize_text(text)
    if len(text) < 15:
        return None
    if non_alpha_ratio(text) > 0.5:
        return None
    if not is_shona(text):
        return None
    return text


def unique_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def fetch_text(session: requests.Session, url: str, log_file: Path, phase: str, timeout: int = 12) -> str | None:
    try:
        response = session.get(url, timeout=timeout)
        if response.status_code >= 400:
            write_log(log_file, "WARN", phase, f"{response.status_code} for {url}")
            return None
        response.encoding = response.encoding or "utf-8"
        return response.text
    except Exception as error:
        write_log(log_file, "WARN", phase, f"Fetch failed for {url}: {error}")
        return None


def fetch_json(session: requests.Session, url: str, log_file: Path, phase: str, timeout: int = 25):
    text = fetch_text(session, url, log_file, phase, timeout=timeout)
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception as error:
        write_log(log_file, "WARN", phase, f"JSON parse failed for {url}: {error}")
        return None


def collect_lines_from_texts(texts: Iterable[str]) -> list[str]:
    lines: list[str] = []
    for text in texts:
        for block in text_blocks(text):
            cleaned = clean_line(block)
            if cleaned:
                lines.append(cleaned)
    return unique_preserve_order(lines)


def extract_reddit_comments(node, collected: list[str]) -> None:
    if isinstance(node, list):
        for child in node:
            extract_reddit_comments(child, collected)
        return
    if not isinstance(node, dict):
        return
    kind = node.get("kind")
    data = node.get("data") or {}
    if kind == "t1":
        body = data.get("body") or ""
        if body:
            collected.append(body)
        replies = data.get("replies")
        if isinstance(replies, dict):
            extract_reddit_comments((replies.get("data") or {}).get("children", []), collected)
    elif kind == "t3":
        selftext = data.get("selftext") or ""
        if selftext:
            collected.append(selftext)


def scrape_reddit(session: requests.Session, log_file: Path) -> dict:
    phase = "PHASE-2"
    write_log(log_file, "INFO", phase, "Starting Reddit JSON collection")
    searches = [
        "https://www.reddit.com/r/zimbabwe/search.json?q=shona&limit=100&sort=top",
        "https://www.reddit.com/r/zimbabwe.json?limit=100",
        "https://www.reddit.com/r/Zimbabwe/search.json?q=chishona&limit=100",
        "https://www.reddit.com/search.json?q=chishona+language&limit=100",
        "https://www.reddit.com/search.json?q=shona+zimbabwe&limit=100",
    ]
    collected: list[str] = []
    seen_posts: set[str] = set()

    for url in searches:
        payload = fetch_json(session, url, log_file, phase)
        if not payload:
            continue
        children = (payload.get("data") or {}).get("children", [])
        for child in children:
            data = child.get("data") or {}
            post_id = data.get("id")
            if not post_id or post_id in seen_posts:
                continue
            seen_posts.add(post_id)
            title = data.get("title") or ""
            selftext = data.get("selftext") or ""
            collected.extend([title, selftext])
            comments_url = f"https://www.reddit.com/comments/{post_id}.json?limit=50&depth=2&raw_json=1"
            comments_payload = fetch_json(session, comments_url, log_file, phase)
            if isinstance(comments_payload, list) and len(comments_payload) > 1:
                extract_reddit_comments((comments_payload[1].get("data") or {}).get("children", []), collected)
        time.sleep(0.2)

    cleaned = collect_lines_from_texts(collected)
    write_log(log_file, "INFO", phase, f"Reddit collected {len(cleaned)} candidate Shona lines")
    return {"name": "reddit", "lines": cleaned, "raw_texts": collected}


def scrape_nitter(session: requests.Session, log_file: Path) -> dict:
    phase = "PHASE-2"
    write_log(log_file, "INFO", phase, "Starting Twitter/X collection via Nitter mirrors")
    instances = [
        "https://nitter.poast.org",
        "https://nitter.privacydev.net",
        "https://nitter.1d4.us",
    ]
    queries = [
        "chiShona",
        "ndiri kufara",
        "ndinoda Zimbabwe",
        "vanhu veZimbabwe",
        "mhoro makadii",
        "ndatenda",
        "zvakanaka",
    ]
    collected: list[str] = []
    for instance in instances:
        for query in queries:
            url = f"{instance}/search?f=tweets&q={quote(query)}"
            html_text = fetch_text(session, url, log_file, phase)
            if not html_text:
                continue
            soup = BeautifulSoup(html_text, "html.parser")
            tweet_nodes = soup.select("div.tweet-content, p.tweet-content, .tweet-content.media-body")
            for node in tweet_nodes:
                text = normalize_text(node.get_text(" ", strip=True))
                if text:
                    collected.append(text)
            time.sleep(0.15)

    cleaned = collect_lines_from_texts(collected)
    write_log(log_file, "INFO", phase, f"Nitter collected {len(cleaned)} candidate Shona lines")
    return {"name": "twitter", "lines": cleaned, "raw_texts": collected}


def facebook_candidate_urls(page_url: str) -> list[str]:
    parsed = urlparse(page_url)
    slug = parsed.path.strip("/")
    base = f"https://mbasic.facebook.com/{slug}" if slug else page_url.rstrip("/")
    return [page_url.rstrip("/"), f"{base}/?v=timeline", f"{base}/posts"]


def scrape_facebook(session: requests.Session, log_file: Path) -> dict:
    phase = "PHASE-2"
    write_log(log_file, "INFO", phase, "Starting Facebook public page collection")
    pages = [
        "https://www.facebook.com/voashona/",
        "https://www.facebook.com/zbcnewsonline/",
        "https://www.facebook.com/263Chat/",
    ]
    google_query = 'site:facebook.com "ndinoda" OR "ndiri" OR "vanhu" Zimbabwe'
    google_url = f"https://www.google.com/search?q={quote(google_query)}&num=20&hl=en"
    collected: list[str] = []

    google_html = fetch_text(session, google_url, log_file, phase)
    if google_html:
        soup = BeautifulSoup(google_html, "html.parser")
        found = 0
        for anchor in soup.select("a[href*='facebook.com']"):
            href = anchor.get("href") or ""
            if href.startswith("/url?q="):
                href = href.split("/url?q=", 1)[1].split("&", 1)[0]
            if href.startswith("http") and "facebook.com" in href:
                found += 1
                pages.append(href)
            if found >= 10:
                break
    else:
        write_log(log_file, "WARN", phase, "Google search for Facebook pages returned nothing")

    seen_urls: set[str] = set()
    for page in pages:
        for candidate_url in facebook_candidate_urls(page):
            if candidate_url in seen_urls:
                continue
            seen_urls.add(candidate_url)
            html_text = fetch_text(session, candidate_url, log_file, phase)
            if not html_text:
                continue
            if "log in" in html_text.lower() and "facebook" in html_text.lower() and "create account" in html_text.lower():
                write_log(log_file, "WARN", phase, f"Facebook login wall for {candidate_url}")
            soup = BeautifulSoup(html_text, "html.parser")
            selectors = [
                "div[data-ad-preview='message']",
                "div[role='article']",
                "article",
                "div[dir='auto']",
            ]
            for selector in selectors:
                for node in soup.select(selector):
                    text = normalize_text(node.get_text(" ", strip=True))
                    if text:
                        collected.append(text)
            time.sleep(0.15)

    cleaned = collect_lines_from_texts(collected)
    write_log(log_file, "INFO", phase, f"Facebook collected {len(cleaned)} candidate Shona lines")
    return {"name": "facebook", "lines": cleaned, "raw_texts": collected}


def youtube_video_id(href: str) -> str | None:
    parsed = urlparse(href)
    query = parse_qs(parsed.query)
    if "v" in query and query["v"]:
        return query["v"][0]
    match = re.search(r"/watch\?v=([A-Za-z0-9_-]{11})", href)
    if match:
        return match.group(1)
    return None


def scrape_youtube(session: requests.Session, log_file: Path) -> dict:
    phase = "PHASE-2"
    write_log(log_file, "INFO", phase, "Starting YouTube search collection")
    queries = [
        "chiShona lessons",
        "shona language Zimbabwe",
        "ndinokudai",
        "munamato weShona",
    ]
    collected: list[str] = []
    seen_videos: set[str] = set()

    for query in queries:
        search_url = f"https://www.youtube.com/results?search_query={quote(query)}&hl=en&gl=ZW"
        html_text = fetch_text(session, search_url, log_file, phase)
        if not html_text:
            continue
        soup = BeautifulSoup(html_text, "html.parser")
        anchors = soup.select("a#video-title, a[href^='/watch']")
        for anchor in anchors:
            href = anchor.get("href") or ""
            video_id = youtube_video_id(href)
            if not video_id or video_id in seen_videos:
                continue
            seen_videos.add(video_id)
            title = normalize_text(anchor.get("title") or anchor.get_text(" ", strip=True))
            watch_url = f"https://www.youtube.com/watch?v={video_id}&hl=en&gl=ZW"
            watch_html = fetch_text(session, watch_url, log_file, phase)
            description = ""
            if watch_html:
                watch_soup = BeautifulSoup(watch_html, "html.parser")
                meta = watch_soup.find("meta", attrs={"name": "description"})
                if meta and meta.get("content"):
                    description = normalize_text(meta.get("content", ""))
            if title:
                collected.append(title)
            if description:
                collected.append(description)
            time.sleep(0.15)

    cleaned = collect_lines_from_texts(collected)
    write_log(log_file, "INFO", phase, f"YouTube collected {len(cleaned)} candidate Shona lines")
    return {"name": "youtube", "lines": cleaned, "raw_texts": collected}


def extract_article_text(html_text: str) -> list[str]:
    soup = BeautifulSoup(html_text, "html.parser")
    texts: list[str] = []
    for meta_name in [("property", "og:title"), ("property", "og:description"), ("name", "description")]:
        meta = soup.find("meta", attrs={meta_name[0]: meta_name[1]})
        if meta and meta.get("content"):
            texts.append(meta["content"])
    for selector in ["article p", "main p", "p"]:
        for node in soup.select(selector):
            text = normalize_text(node.get_text(" ", strip=True))
            if len(text) >= 20:
                texts.append(text)
    return texts


def is_same_domain(url: str, domain: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc.endswith(domain) or parsed.netloc == domain


def prioritize_site_links(base_url: str, links: list[str]) -> list[str]:
    base_domain = urlparse(base_url).netloc
    scored: list[tuple[int, str]] = []
    seen: set[str] = set()
    for link in links:
        absolute = urljoin(base_url, link)
        if absolute in seen:
            continue
        seen.add(absolute)
        parsed = urlparse(absolute)
        if not is_same_domain(absolute, base_domain):
            continue
        path = parsed.path.lower()
        score = 0
        if any(token in path for token in ("shona", "chi", "zimbabwe", "culture", "news", "article", "story")):
            score += 3
        if re.search(r"/\d{4}/\d{2}/", path):
            score += 2
        if len(path) > 1:
            score += 1
        scored.append((score, absolute))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [url for _, url in scored]


def scrape_generic_site(session: requests.Session, site_url: str, site_key: str, log_file: Path) -> dict:
    phase = "PHASE-2"
    write_log(log_file, "INFO", phase, f"Starting website crawl for {site_key}")
    homepage = fetch_text(session, site_url, log_file, phase)
    collected: list[str] = []
    if not homepage:
        write_log(log_file, "WARN", phase, f"Homepage unavailable for {site_key}")
        return {"name": site_key, "lines": [], "raw_texts": []}

    soup = BeautifulSoup(homepage, "html.parser")
    anchors = [anchor.get("href") for anchor in soup.find_all("a", href=True)]
    anchors = [href for href in anchors if href]
    prioritized = prioritize_site_links(site_url, anchors)
    article_urls = prioritized[:6]
    article_urls.insert(0, site_url)
    article_urls = unique_preserve_order(article_urls)

    for article_url in article_urls[:6]:
        html_text = fetch_text(session, article_url, log_file, phase)
        if not html_text:
            continue
        collected.extend(extract_article_text(html_text))
        time.sleep(0.1)

    cleaned = collect_lines_from_texts(collected)
    write_log(log_file, "INFO", phase, f"{site_key} collected {len(cleaned)} candidate Shona lines")
    return {"name": site_key, "lines": cleaned, "raw_texts": collected}


def scrape_telegram(session: requests.Session, log_file: Path) -> dict:
    phase = "PHASE-2"
    write_log(log_file, "INFO", phase, "Starting Telegram public channel collection")
    channels = [
        "https://t.me/s/zimbabwe",
        "https://t.me/s/chiShona",
        "https://t.me/s/voashona",
    ]
    collected: list[str] = []
    for channel in channels:
        html_text = fetch_text(session, channel, log_file, phase)
        if not html_text:
            continue
        soup = BeautifulSoup(html_text, "html.parser")
        for selector in ["div.tgme_widget_message_text", "div.tgme_widget_message_text.js-message_text"]:
            for node in soup.select(selector):
                text = normalize_text(node.get_text(" ", strip=True))
                if text:
                    collected.append(text)
        time.sleep(0.1)

    cleaned = collect_lines_from_texts(collected)
    write_log(log_file, "INFO", phase, f"Telegram collected {len(cleaned)} candidate Shona lines")
    return {"name": "telegram", "lines": cleaned, "raw_texts": collected}


def dedupe_against_corpus(existing_lines: set[str], candidate_lines: Iterable[str]) -> list[str]:
    new_lines: list[str] = []
    seen_new: set[str] = set()
    for line in candidate_lines:
        normalized = normalize_text(line)
        if not normalized or normalized in existing_lines or normalized in seen_new:
            continue
        seen_new.add(normalized)
        new_lines.append(normalized)
    return new_lines


def count_tokens(lines: Iterable[str]) -> int:
    return sum(len(line.split()) for line in lines)


def save_lines(path: Path, lines: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for line in lines:
            handle.write(normalize_text(line) + "\n")


def update_manifest(entries: list[dict], log_file: Path) -> None:
    manifest = load_json(MANIFEST_FILE, [])
    if not isinstance(manifest, list):
        manifest = []
    manifest.extend(entries)
    save_json(MANIFEST_FILE, manifest)
    write_log(log_file, "INFO", "PHASE-2", f"Manifest updated with {len(entries)} source entries")


def regenerate_splits(all_lines: list[str]) -> dict:
    shuffled = list(all_lines)
    random.Random(42).shuffle(shuffled)
    total = len(shuffled)
    train_end = int(total * 0.98)
    valid_end = int(total * 0.99)
    train_lines = shuffled[:train_end]
    valid_lines = shuffled[train_end:valid_end]
    test_lines = shuffled[valid_end:]

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    save_lines(TRAIN_FILE, train_lines)
    save_lines(VALID_FILE, valid_lines)
    save_lines(TEST_FILE, test_lines)

    stats = {
        "total_lines": total,
        "total_tokens": count_tokens(shuffled),
        "train_lines": len(train_lines),
        "valid_lines": len(valid_lines),
        "test_lines": len(test_lines),
        "train_tokens": count_tokens(train_lines),
        "valid_tokens": count_tokens(valid_lines),
        "test_tokens": count_tokens(test_lines),
    }
    save_json(STATS_FILE, stats)
    return stats


def update_state(run_totals: dict, successful_sources: list[str], log_file: Path, commit_message: str | None = None) -> None:
    state = load_json(STATE_FILE, {})
    if not isinstance(state, dict):
        state = {}
    state.setdefault("project", "shona-ai")
    state.setdefault("version", "0.1.0")
    state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    state["agent_number"] = 17
    state["model_used"] = "GPT-5.4 mini"
    state["current_phase"] = 2
    phase_status = state.get("phase_status") if isinstance(state.get("phase_status"), dict) else {}
    phase_status["2"] = "complete"
    state["phase_status"] = phase_status
    data_stats = state.get("data_stats") if isinstance(state.get("data_stats"), dict) else {}
    data_stats["raw_tokens"] = run_totals["raw_tokens"]
    data_stats["clean_tokens"] = run_totals["clean_tokens"]
    data_stats["sources_complete"] = unique_preserve_order((data_stats.get("sources_complete") or []) + successful_sources)
    state["data_stats"] = data_stats
    state["next_action"] = "Review social/web scraping results, then move into phase 3 cleaning and filtering."
    if commit_message:
        state["last_commit"] = commit_message
    save_json(STATE_FILE, state)
    write_log(log_file, "INFO", "PHASE-2", "STATE.json updated")


def show_source_samples(log_file: Path, source_name: str, lines: list[str]) -> None:
    if not lines:
        write_log(log_file, "WARN", "PHASE-2", f"{source_name} yielded no clean Shona lines")
        return
    write_log(log_file, "MILESTONE", "PHASE-2", f"{source_name} sample lines before append:")
    for index, line in enumerate(lines[:5], start=1):
        write_log(log_file, "MILESTONE", "PHASE-2", f"{source_name} sample {index}: {line}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Shona social and web sources into the corpus.")
    parser.add_argument("--log-file", type=Path, default=DEFAULT_LOG_FILE, help="Path to the session log file.")
    args = parser.parse_args()

    log_file = args.log_file
    session = build_session()
    write_log(log_file, "INFO", "PHASE-2", "Agent 17 social/web scraping sprint started")

    existing_lines = set()
    if ALL_CLEAN_FILE.exists():
        with open(ALL_CLEAN_FILE, "r", encoding="utf-8") as handle:
            existing_lines = {normalize_text(line) for line in handle if normalize_text(line)}
    write_log(log_file, "INFO", "PHASE-2", f"Loaded {len(existing_lines):,} existing corpus lines for dedupe")

    source_specs = [
        ("reddit", scrape_reddit, RAW_DIR / "social" / "reddit_shona.txt"),
        ("twitter", scrape_nitter, RAW_DIR / "social" / "twitter_shona.txt"),
        ("facebook", scrape_facebook, RAW_DIR / "social" / "facebook_shona.txt"),
        ("youtube", scrape_youtube, RAW_DIR / "social" / "youtube_shona.txt"),
        ("telegram", scrape_telegram, RAW_DIR / "social" / "telegram_shona.txt"),
    ]

    news_specs = [
        ("masvingo_mirror", "https://www.masvingomirror.com", RAW_DIR / "news" / "masvingomirror_shona.txt"),
        ("zimetro", "https://www.zimetro.co.zw", RAW_DIR / "news" / "zimetro_shona.txt"),
        ("myzimbabwe", "https://www.myzimbabwe.co.zw", RAW_DIR / "news" / "myzimbabwe_shona.txt"),
        ("nehanda_radio", "https://nehanda.radio", RAW_DIR / "news" / "nehanda_radio_shona.txt"),
        ("newsday", "https://www.newsday.co.zw", RAW_DIR / "news" / "newsday_shona.txt"),
        ("sunday_mail", "https://www.sundaymail.co.zw", RAW_DIR / "news" / "sundaymail_shona.txt"),
        ("chronicle", "https://www.chronicle.co.zw", RAW_DIR / "news" / "chronicle_shona.txt"),
    ]

    results: list[dict] = []
    for source_name, collector, output_path in source_specs:
        try:
            result = collector(session, log_file)
            results.append(result)
            save_lines(output_path, result["lines"])
            write_log(log_file, "INFO", "PHASE-2", f"{source_name} raw output written to {output_path}")
        except Exception as error:
            write_log(log_file, "ERROR", "PHASE-2", f"{source_name} collection failed: {error}")

    for site_key, site_url, output_path in news_specs:
        try:
            result = scrape_generic_site(session, site_url, site_key, log_file)
            results.append(result)
            save_lines(output_path, result["lines"])
            write_log(log_file, "INFO", "PHASE-2", f"{site_key} raw output written to {output_path}")
        except Exception as error:
            write_log(log_file, "ERROR", "PHASE-2", f"{site_key} collection failed: {error}")

    successful_sources: list[str] = []
    new_lines_by_source: dict[str, list[str]] = {}
    raw_token_total = 0
    clean_token_total = 0

    for result in results:
        source_name = result["name"]
        raw_lines = unique_preserve_order(result.get("lines", []))
        new_lines = dedupe_against_corpus(existing_lines, raw_lines)
        if not new_lines:
            write_log(log_file, "WARN", "PHASE-2", f"{source_name} produced no new corpus lines after dedupe")
            continue
        show_source_samples(log_file, source_name, new_lines)
        successful_sources.append(source_name)
        new_lines_by_source[source_name] = new_lines
        raw_token_total += count_tokens(raw_lines)
        clean_token_total += count_tokens(new_lines)
        existing_lines.update(new_lines)

    appended_lines: list[str] = []
    for source_name, _collector, _path in source_specs:
        appended_lines.extend(new_lines_by_source.get(source_name, []))
    for site_key, _site_url, _path in news_specs:
        appended_lines.extend(new_lines_by_source.get(site_key, []))

    if appended_lines:
        ALL_CLEAN_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ALL_CLEAN_FILE, "a", encoding="utf-8") as handle:
            for line in appended_lines:
                handle.write(line + "\n")
        write_log(log_file, "MILESTONE", "PHASE-2", f"Appended {len(appended_lines):,} new unique lines to {ALL_CLEAN_FILE}")
    else:
        write_log(log_file, "WARN", "PHASE-2", "No new lines appended to all_clean.txt")

    stats = regenerate_splits(sorted(existing_lines))
    write_log(
        log_file,
        "MILESTONE",
        "PHASE-2",
        f"Splits regenerated: total_lines={stats['total_lines']:,}, total_tokens={stats['total_tokens']:,}",
    )

    update_manifest(
        [
            {
                "source": result["name"],
                "tokens": count_tokens(result.get("lines", [])),
                "docs": len(result.get("lines", [])),
                "path": str(next((path for name, _, path in source_specs + news_specs if name == result["name"]), RAW_DIR / "social" / f"{result['name']}.txt")),
                "downloaded_at": datetime.now().isoformat(),
            }
            for result in results
        ],
        log_file,
    )

    run_totals = {
        "raw_tokens": raw_token_total,
        "clean_tokens": stats["total_tokens"],
    }
    update_state(run_totals, successful_sources, log_file, commit_message="feat: social media and web scraping sprint")

    summary_lines = [
        "SOURCE SUMMARY",
        f"reddit: {'success' if 'reddit' in successful_sources else 'failed'}",
        f"twitter: {'success' if 'twitter' in successful_sources else 'failed'}",
        f"facebook: {'success' if 'facebook' in successful_sources else 'failed'}",
        f"youtube: {'success' if 'youtube' in successful_sources else 'failed'}",
        f"telegram: {'success' if 'telegram' in successful_sources else 'failed'}",
    ]
    for site_key, _site_url, _path in news_specs:
        summary_lines.append(f"{site_key}: {'success' if site_key in successful_sources else 'failed'}")
    summary_lines.append(f"new raw tokens: {raw_token_total:,}")
    summary_lines.append(f"new clean tokens: {clean_token_total:,}")
    summary_lines.append(f"final corpus tokens: {stats['total_tokens']:,}")
    for line in summary_lines:
        write_log(log_file, "MILESTONE", "PHASE-2", line)

    print("\n".join(summary_lines))


if __name__ == "__main__":
    main()