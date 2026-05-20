"""Data cleaning pipeline placeholder."""
import json
import random
import re
import unicodedata
from functools import lru_cache
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Iterable

from langdetect import DetectorFactory, detect_langs


DetectorFactory.seed = 42

SHONA_HINTS = (
    "kuti",
    "uye",
    "kana",
    "zvino",
    "pane",
    "muna",
    "ichi",
    "icho",
    "avo",
    "aya",
    "ndiye",
    "nhasi",
    "asi",
)

SHONA_COMMON_WORDS = {
    "mwari",
    "akati",
    "kuti",
    "uye",
    "kana",
    "izvozvo",
    "zvino",
    "munhu",
    "vanhu",
    "nyika",
    "denga",
    "chiedza",
    "rima",
    "mvura",
    "zuva",
    "usiku",
    "namangwanani",
    "madeko",
    "nhasi",
    "ndiye",
    "kwake",
    "kwavo",
    "kwatiri",
    "jesu",
    "allah",
    "isu",
    "yake",
    "zvake",
    "akaita",
    "akanga",
}

NOW = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / f"{NOW}_agent3.log"

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
RAW_MANIFEST = RAW_DIR / "manifest.json"
STATS_FILE = PROCESSED_DIR / "stats.json"
PROCESSED_MANIFEST = PROCESSED_DIR / "manifest.json"


@dataclass(frozen=True)
class SourceSpec:
    name: str
    raw_path: Path
    kind: str


SOURCE_SPECS = [
    SourceSpec("wikipedia_sn", RAW_DIR / "wikipedia" / "shona_wiki.txt", "text"),
    SourceSpec("cc100_sn", RAW_DIR / "cc100" / "shona_cc100.txt", "text"),
    SourceSpec("bible_shona", RAW_DIR / "bible" / "shona_bible.txt", "xml"),
    SourceSpec("opus_en_sn", RAW_DIR / "opus" / "en-sn_parallel.txt", "parallel"),
]


def write_log(level: str, phase: str, message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{level}] [{phase}] {message}"
    print(entry)
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(entry + "\n")


def load_raw_manifest() -> list[dict]:
    if not RAW_MANIFEST.exists():
        return []
    with open(RAW_MANIFEST, "r", encoding="utf-8") as handle:
        return json.load(handle)


def build_source_paths() -> dict[str, Path]:
    latest_by_source: dict[str, Path] = {}
    for entry in load_raw_manifest():
        source = entry.get("source")
        path = entry.get("path")
        if source and path:
            latest_by_source[source] = Path(path)
    for spec in SOURCE_SPECS:
        latest_by_source.setdefault(spec.name, spec.raw_path)
    return latest_by_source


def normalize_text(text: str) -> str:
    text = unescape(text)
    text = unicodedata.normalize("NFC", unicodedata.normalize("NFD", text))
    text = re.sub(r"<ref[^>]*>.*?</ref>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\{\{[^{}]*\}\}", " ", text)
    text = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]+)\]\]', r'\1', text)
    text = re.sub(r'\[\[(?:[^\]]*?)\]\]', ' ', text)
    text = re.sub(r"[\{\}\[\]\|]", " ", text)
    text = re.sub(r"^\s*[\*=#:;!]+\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_html_artifacts(text: str) -> str:
    text = re.sub(r"(?i)&nbsp;|&amp;|&lt;|&gt;", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\b(?:File|Image):\S+", " ", text)
    text = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def looks_like_shona(text: str) -> bool:
    lower_text = f" {text.casefold()} "
    hint_hits = sum(1 for hint in SHONA_HINTS if f" {hint} " in lower_text)
    if hint_hits >= 1:
        return True
    if "zh" in lower_text or "http" in lower_text:
        return False
    return len(text.split()) >= 6 and any(token.endswith(("ka", "wa", "ya", "vo", "zo", "no")) for token in text.casefold().split())


def shona_lexical_score(text: str) -> int:
    tokens = re.findall(r"[a-zA-Z]+", text.casefold())
    if not tokens:
        return 0
    return sum(1 for token in tokens if token in SHONA_COMMON_WORDS)


@lru_cache(maxsize=32768)
def detect_shona_probability(sample: str) -> float:
    try:
        guesses = detect_langs(sample[:240])
    except Exception:
        return 0.0
    for guess in guesses:
        if guess.lang == "sn":
            return guess.prob
    return 0.0


def is_probably_shona(text: str) -> bool:
    if len(text) < 20:
        return False
    word_count = len(text.split())
    if word_count < 3:
        return False
    alpha_count = sum(char.isalpha() for char in text)
    if alpha_count / max(len(text), 1) < 0.55:
        return False
    digit_count = sum(char.isdigit() for char in text)
    if digit_count / max(len(text), 1) > 0.20:
        return False
    if shona_lexical_score(text) >= 1:
        return True
    if not looks_like_shona(text):
        return False
    return detect_shona_probability(text) >= 0.20


def extract_candidates(source: SourceSpec, raw_text: str) -> Iterable[str]:
    if source.kind == "parallel":
        for line in raw_text.splitlines():
            if "\t" in line:
                _, shona_text = line.split("\t", 1)
                yield shona_text
    else:
        for line in raw_text.splitlines():
            yield line


def clean_candidate(text: str) -> str:
    text = normalize_text(text)
    text = strip_html_artifacts(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def read_source_text(path: Path) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        return handle.read()


def clean_source(spec: SourceSpec, global_seen: set[str]) -> dict:
    if not spec.raw_path.exists():
        write_log("WARN", "PHASE-3", f"Missing raw source: {spec.raw_path}")
        return {
            "source": spec.name,
            "input_lines": 0,
            "output_lines": 0,
            "removed_duplicates": 0,
            "removed_language": 0,
            "removed_junk": 0,
            "output_path": None,
        }

    write_log("INFO", "PHASE-3", f"Cleaning source {spec.name} from {spec.raw_path}")
    raw_text = read_source_text(spec.raw_path)
    raw_lines = raw_text.splitlines()
    candidate_count = 0
    cleaned_lines: list[str] = []
    source_seen: set[str] = set()
    removed_language = 0
    removed_junk = 0
    removed_duplicates = 0

    for candidate in extract_candidates(spec, raw_text):
        candidate_count += 1
        cleaned = clean_candidate(candidate)
        if not cleaned:
            removed_junk += 1
            continue
        if not is_probably_shona(cleaned):
            removed_language += 1
            continue
        normalized_key = cleaned.casefold()
        if normalized_key in source_seen or normalized_key in global_seen:
            removed_duplicates += 1
            continue
        source_seen.add(normalized_key)
        global_seen.add(normalized_key)
        cleaned_lines.append(cleaned)

    output_path = PROCESSED_DIR / f"{spec.name}.clean.txt"
    with open(output_path, "w", encoding="utf-8") as handle:
        for line in cleaned_lines:
            handle.write(line + "\n")

    write_log(
        "MILESTONE",
        "PHASE-3",
        f"{spec.name} cleaned: {len(cleaned_lines)} lines kept from {candidate_count}; removed language={removed_language}, junk={removed_junk}, duplicates={removed_duplicates}",
    )
    return {
        "source": spec.name,
        "input_lines": candidate_count,
        "output_lines": len(cleaned_lines),
        "removed_duplicates": removed_duplicates,
        "removed_language": removed_language,
        "removed_junk": removed_junk,
        "output_path": str(output_path),
    }


def write_processed_manifest(results: list[dict]) -> None:
    with open(PROCESSED_MANIFEST, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, ensure_ascii=False)


def build_combined_corpus(results: list[dict]) -> list[str]:
    combined_lines: list[str] = []
    for result in results:
        output_path = result.get("output_path")
        if not output_path:
            continue
        with open(output_path, "r", encoding="utf-8") as handle:
            combined_lines.extend(line.strip() for line in handle if line.strip())
    return combined_lines


def write_splits(lines: list[str]) -> dict[str, int]:
    random.Random(42).shuffle(lines)
    total = len(lines)
    train_end = int(total * 0.98)
    valid_end = int(total * 0.99)
    split_map = {
        "train": lines[:train_end],
        "valid": lines[train_end:valid_end],
        "test": lines[valid_end:],
    }
    for split_name, split_lines in split_map.items():
        with open(PROCESSED_DIR / f"{split_name}.txt", "w", encoding="utf-8") as handle:
            for line in split_lines:
                handle.write(line + "\n")
    return {name: len(lines) for name, lines in split_map.items()}


def main() -> None:
    write_log("INFO", "PHASE-3", "Agent 3: clean_data.py started")
    source_paths = build_source_paths()
    global_seen: set[str] = set()
    results: list[dict] = []

    for spec in SOURCE_SPECS:
        cleaned_result = clean_source(
            SourceSpec(spec.name, source_paths.get(spec.name, spec.raw_path), spec.kind),
            global_seen,
        )
        results.append(cleaned_result)

    write_processed_manifest(results)
    combined_lines = build_combined_corpus(results)
    with open(PROCESSED_DIR / "all_clean.txt", "w", encoding="utf-8") as handle:
        for line in combined_lines:
            handle.write(line + "\n")
    split_counts = write_splits(combined_lines.copy())

    clean_tokens = sum(len(line.split()) for line in combined_lines)
    stats = {
        "created_at": datetime.now().isoformat(),
        "sources": results,
        "combined": {
            "lines": len(combined_lines),
            "tokens": clean_tokens,
        },
        "splits": split_counts,
    }
    with open(STATS_FILE, "w", encoding="utf-8") as handle:
        json.dump(stats, handle, indent=2, ensure_ascii=False)

    write_log("MILESTONE", "PHASE-3", f"Cleaning complete: {len(combined_lines)} lines, ~{clean_tokens:,} tokens")


if __name__ == "__main__":
    main()
