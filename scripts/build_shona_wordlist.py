"""Build a Shona wordlist from FreeDict and Wiktionary sources."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup


OUTPUT_FILE = Path("data/dictionaries/shona_words.txt")
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

FREEDICT_CANDIDATE_URLS = [
    "https://raw.githubusercontent.com/freedict/fd-dictionaries/master/sn-en/sn-en.tei",
    "https://raw.githubusercontent.com/freedict/fd-dictionaries/master/sn-en/sn-en.tei.xml",
    "https://raw.githubusercontent.com/freedict/fd-dictionaries/master/sn-eng/sn-eng.tei",
    "https://raw.githubusercontent.com/freedict/fd-dictionaries/master/sna-eng/sna-eng.tei",
    "https://raw.githubusercontent.com/freedict/fd-dictionaries/master/eng-sn/eng-sn.tei",
    "https://raw.githubusercontent.com/freedict/fd-dictionaries/master/eng-sna/eng-sna.tei",
]

WIKTIONARY_CATEGORY_URL = "https://en.wiktionary.org/wiki/Category:Shona_lemmas"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ShonaAI/1.0 (wordlist builder)",
    "Accept-Language": "en-US,en;q=0.9",
}


def normalize_word(word: str) -> str:
    word = unicodedata.normalize("NFC", word).strip()
    word = re.sub(r"\s+", " ", word)
    return word


def fetch_text(url: str) -> str:
    response = requests.get(url, timeout=60, headers=REQUEST_HEADERS)
    response.raise_for_status()
    return response.text


def parse_freedict_tei(xml_text: str) -> set[str]:
    words: set[str] = set()
    root = ET.fromstring(xml_text)
    for orth in root.findall(".//{*}orth"):
        if orth.text:
            word = normalize_word(orth.text)
            if word:
                words.add(word)
    return words


def extract_wiktionary_pages(html_text: str) -> tuple[set[str], str | None]:
    soup = BeautifulSoup(html_text, "lxml")
    words: set[str] = set()

    category_area = soup.select_one("div#mw-pages") or soup.select_one("div.mw-category") or soup
    for link in category_area.select("a[href]"):
        href = link.get("href", "")
        text = normalize_word(link.get_text(strip=True))
        if not text:
            continue
        if href.startswith("/wiki/") and not href.startswith("/wiki/Category:") and not href.startswith("/wiki/Special:"):
            if text not in {"next page", "previous page"}:
                words.add(text)

    next_link = soup.find("a", string=re.compile(r"next page", re.I))
    if next_link and next_link.get("href"):
        return words, urljoin("https://en.wiktionary.org", next_link["href"])
    rel_next = soup.find("a", attrs={"rel": "next"})
    if rel_next and rel_next.get("href"):
        return words, urljoin("https://en.wiktionary.org", rel_next["href"])
    return words, None


def build_wiktionary_wordlist() -> set[str]:
    words: set[str] = set()
    next_url: str | None = WIKTIONARY_CATEGORY_URL
    visited: set[str] = set()

    while next_url and next_url not in visited:
        visited.add(next_url)
        html_text = fetch_text(next_url)
        page_words, next_url = extract_wiktionary_pages(html_text)
        words.update(page_words)

    return words


def build_freedict_wordlist() -> set[str]:
    last_error: Exception | None = None
    for url in FREEDICT_CANDIDATE_URLS:
        try:
            xml_text = fetch_text(url)
            words = parse_freedict_tei(xml_text)
            if words:
                print(f"FreeDict source loaded from {url}: {len(words)} words")
                return words
        except Exception as exc:
            last_error = exc
            print(f"FreeDict source unavailable at {url}: {exc}")
    if last_error:
        print(f"FreeDict source not found; continuing with Wiktionary only: {last_error}")
    return set()


def main() -> None:
    words = build_freedict_wordlist()
    words.update(build_wiktionary_wordlist())
    normalized_words = sorted({normalize_word(word) for word in words if normalize_word(word)})

    with open(OUTPUT_FILE, "w", encoding="utf-8") as handle:
        for word in normalized_words:
            handle.write(word + "\n")

    print(f"Wrote {len(normalized_words)} words to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()