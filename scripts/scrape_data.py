import os
import json
import logging
from pathlib import Path
from datetime import datetime
import requests
import xml.etree.ElementTree as ET

from datasets import load_dataset


NOW = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / f"{NOW}_agent2.log"

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_FILE = RAW_DIR / "manifest.json"


def write_log(level, phase, message):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] [{level}] [{phase}] {message}"
    print(entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


def update_manifest(entry: dict):
    manifest = []
    if MANIFEST_FILE.exists():
        try:
            with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            manifest = []
    manifest.append({**entry, "downloaded_at": datetime.now().isoformat()})
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    write_log("MILESTONE", "PHASE-2", f"Manifest updated for {entry.get('source')}")


def save_text_lines(path: Path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for l in lines:
            f.write(l.replace("\r", "") + "\n")


def count_tokens_in_lines(lines):
    return sum(len(l.split()) for l in lines)


def download_wikipedia_shona():
    write_log("INFO", "PHASE-2", "Starting Wikipedia Shona download via datasets")
    try:
        ds = load_dataset("wikipedia", "20231101.sn", split="train", trust_remote_code=True)
        texts = [item["text"].strip() for item in ds if item.get("text")]
        output_path = RAW_DIR / "wikipedia" / "shona_wiki.txt"
        save_text_lines(output_path, texts)
        token_est = count_tokens_in_lines(texts)
        res = {"source": "wikipedia_sn", "tokens": token_est, "docs": len(texts), "path": str(output_path)}
        write_log("MILESTONE", "PHASE-2", f"Wikipedia complete: {len(texts)} articles, ~{token_est:,} tokens")
        return res
    except Exception as e:
        write_log("ERROR", "PHASE-2", f"Wikipedia download failed: {e}")
        raise


def download_cc100_shona():
    write_log("INFO", "PHASE-2", "Starting CC-100 Shona download (streaming)")
    output_path = RAW_DIR / "cc100" / "shona_cc100.txt"
    try:
        ds = load_dataset("cc100", lang="sn", split="train", streaming=True)
        lines = []
        count = 0
        token_count = 0
        for item in ds:
            text = item.get("text") or item.get("content") or ""
            text = text.strip()
            if not text:
                continue
            lines.append(text)
            token_count += len(text.split())
            count += 1
            if count % 10000 == 0:
                write_log("INFO", "PHASE-2", f"CC-100: {count:,} docs, ~{token_count:,} tokens")
        save_text_lines(output_path, lines)
        write_log("MILESTONE", "PHASE-2", f"CC-100 complete: {count:,} docs, ~{token_count:,} tokens")
        return {"source": "cc100_sn", "tokens": token_count, "docs": count, "path": str(output_path)}
    except Exception as e:
        write_log("ERROR", "PHASE-2", f"CC-100 download failed: {e}")
        raise


def download_bible_shona():
    write_log("INFO", "PHASE-2", "Starting Shona Bible download from GitHub raw")
    url = "https://raw.githubusercontent.com/christos-c/bible-corpus/master/bibles/Shona.xml"
    output_path = RAW_DIR / "bible" / "shona_bible.txt"
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        content = r.content
        # Parse XML and extract verses/text
        try:
            root = ET.fromstring(content)
            verses = []
            # Find all text nodes under <chapter>/<verse> or similar
            for elem in root.iter():
                if elem.tag.lower().endswith("verse") or elem.tag.lower().endswith("text"):
                    text = (elem.text or "").strip()
                    if text:
                        verses.append(text)
            # Fallback: if none found, use raw text split
            if not verses:
                verses = [line.strip() for line in content.decode("utf-8", errors="ignore").splitlines() if line.strip()]
        except Exception:
            verses = [line.strip() for line in content.decode("utf-8", errors="ignore").splitlines() if line.strip()]
        save_text_lines(output_path, verses)
        token_est = count_tokens_in_lines(verses)
        write_log("MILESTONE", "PHASE-2", f"Bible download complete: ~{token_est:,} tokens, {len(verses)} lines")
        return {"source": "bible_shona", "tokens": token_est, "docs": len(verses), "path": str(output_path)}
    except Exception as e:
        write_log("ERROR", "PHASE-2", f"Bible download failed: {e}")
        raise


def download_opus_en_sn():
    write_log("INFO", "PHASE-2", "Starting OPUS parallel (en-sn) download via datasets")
    output_path = RAW_DIR / "opus" / "en-sn_parallel.txt"
    try:
        # Try several dataset names that may contain en-sn
        candidates = [
            ("Helsinki-NLP/opus-100", "en-sn"),
            ("opus_books", None),
            ("Helsinki-NLP/ccaligned_v1", None),
        ]
        lines = []
        total_pairs = 0
        for name, config in candidates:
            try:
                if config:
                    ds = load_dataset(name, config, split="train")
                else:
                    ds = load_dataset(name, split="train")
                # Attempt to extract parallel pairs
                for item in ds:
                    # Try common keys
                    en = item.get("translation", {}).get("en") if isinstance(item.get("translation"), dict) else item.get("en")
                    sn = None
                    if isinstance(item.get("translation"), dict):
                        sn = item.get("translation", {}).get("sn")
                    sn = sn or item.get("sn") or item.get("translation_sn")
                    if not en or not sn:
                        # Try fields like "text" for bitext corpora (simpler fallback)
                        en = en or item.get("text")
                        sn = sn or item.get("text_sn")
                    if en and sn:
                        lines.append(en.strip() + "\t" + sn.strip())
                        total_pairs += 1
                        if total_pairs % 10000 == 0:
                            write_log("INFO", "PHASE-2", f"OPUS: {total_pairs:,} pairs collected")
            except Exception as e:
                write_log("WARN", "PHASE-2", f"OPUS candidate {name} failed: {e}")
                continue
        save_text_lines(output_path, lines)
        token_est = sum(len(pair.split()) for pair in lines)
        write_log("MILESTONE", "PHASE-2", f"OPUS complete: {total_pairs:,} pairs, ~{token_est:,} tokens")
        return {"source": "opus_en_sn", "tokens": token_est, "docs": total_pairs, "path": str(output_path)}
    except Exception as e:
        write_log("ERROR", "PHASE-2", f"OPUS download failed: {e}")
        raise


def main():
    write_log("INFO", "PHASE-2", "Agent 2: scrape_data.py started")
    funcs = [
        (download_wikipedia_shona, "wikipedia_sn"),
        (download_cc100_shona, "cc100_sn"),
        (download_bible_shona, "bible_shona"),
        (download_opus_en_sn, "opus_en_sn"),
    ]
    results = []
    for fn, name in funcs:
        try:
            res = fn()
            results.append(res)
            update_manifest(res)
            # After each source, write a small checkpoint log
            write_log("MILESTONE", "PHASE-2", f"Source {name} downloaded - ~{res.get('tokens',0):,} tokens")
        except Exception as e:
            write_log("ERROR", "PHASE-2", f"Source {name} failed: {e}")
            # continue to next source
            continue

    total_tokens = sum(r.get("tokens", 0) for r in results)
    write_log("MILESTONE", "PHASE-2", f"All scraping complete. Total tokens: ~{total_tokens:,}")


if __name__ == "__main__":
    main()
import os
import json
import logging
from pathlib import Path
from datetime import datetime
import requests
import xml.etree.ElementTree as ET

from datasets import load_dataset


NOW = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / f"{NOW}_agent2.log"

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_FILE = RAW_DIR / "manifest.json"


def write_log(level, phase, message):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] [{level}] [{phase}] {message}"
    print(entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


def update_manifest(entry: dict):
    manifest = []
    if MANIFEST_FILE.exists():
        try:
            with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            manifest = []
    manifest.append({**entry, "downloaded_at": datetime.now().isoformat()})
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    write_log("MILESTONE", "PHASE-2", f"Manifest updated for {entry.get('source')}")


def save_text_lines(path: Path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for l in lines:
            f.write(l.replace("\r", "") + "\n")


def count_tokens_in_lines(lines):
    return sum(len(l.split()) for l in lines)


def download_wikipedia_shona():
    write_log("INFO", "PHASE-2", "Starting Wikipedia Shona download via datasets")
    try:
        ds = load_dataset("wikipedia", "20231101.sn", split="train", trust_remote_code=True)
        texts = [item["text"].strip() for item in ds if item.get("text")]
        output_path = RAW_DIR / "wikipedia" / "shona_wiki.txt"
        save_text_lines(output_path, texts)
        token_est = count_tokens_in_lines(texts)
        res = {"source": "wikipedia_sn", "tokens": token_est, "docs": len(texts), "path": str(output_path)}
        write_log("MILESTONE", "PHASE-2", f"Wikipedia complete: {len(texts)} articles, ~{token_est:,} tokens")
        return res
    except Exception as e:
        write_log("ERROR", "PHASE-2", f"Wikipedia download failed: {e}")
        raise


def download_cc100_shona():
    write_log("INFO", "PHASE-2", "Starting CC-100 Shona download (streaming)")
    output_path = RAW_DIR / "cc100" / "shona_cc100.txt"
    try:
        ds = load_dataset("cc100", lang="sn", split="train", streaming=True)
        lines = []
        count = 0
        token_count = 0
        for item in ds:
            text = item.get("text") or item.get("content") or ""
            text = text.strip()
            if not text:
                continue
            lines.append(text)
            token_count += len(text.split())
            count += 1
            if count % 10000 == 0:
                write_log("INFO", "PHASE-2", f"CC-100: {count:,} docs, ~{token_count:,} tokens")
        save_text_lines(output_path, lines)
        write_log("MILESTONE", "PHASE-2", f"CC-100 complete: {count:,} docs, ~{token_count:,} tokens")
        return {"source": "cc100_sn", "tokens": token_count, "docs": count, "path": str(output_path)}
    except Exception as e:
        write_log("ERROR", "PHASE-2", f"CC-100 download failed: {e}")
        raise


def download_bible_shona():
    write_log("INFO", "PHASE-2", "Starting Shona Bible download from GitHub raw")
    url = "https://raw.githubusercontent.com/christos-c/bible-corpus/master/bibles/Shona.xml"
    output_path = RAW_DIR / "bible" / "shona_bible.txt"
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        content = r.content
        # Parse XML and extract verses/text
        try:
            root = ET.fromstring(content)
            verses = []
            # Find all text nodes under <chapter>/<verse> or similar
            for elem in root.iter():
                if elem.tag.lower().endswith("verse") or elem.tag.lower().endswith("text"):
                    text = (elem.text or "").strip()
                    if text:
                        verses.append(text)
            # Fallback: if none found, use raw text split
            if not verses:
                verses = [line.strip() for line in content.decode("utf-8", errors="ignore").splitlines() if line.strip()]
        except Exception:
            verses = [line.strip() for line in content.decode("utf-8", errors="ignore").splitlines() if line.strip()]
        save_text_lines(output_path, verses)
        token_est = count_tokens_in_lines(verses)
        write_log("MILESTONE", "PHASE-2", f"Bible download complete: ~{token_est:,} tokens, {len(verses)} lines")
        return {"source": "bible_shona", "tokens": token_est, "docs": len(verses), "path": str(output_path)}
    except Exception as e:
        write_log("ERROR", "PHASE-2", f"Bible download failed: {e}")
        raise


def download_opus_en_sn():
    write_log("INFO", "PHASE-2", "Starting OPUS parallel (en-sn) download via datasets")
    output_path = RAW_DIR / "opus" / "en-sn_parallel.txt"
    try:
        # Try several dataset names that may contain en-sn
        candidates = [
            ("Helsinki-NLP/opus-100", "en-sn"),
            ("opus_books", None),
            ("Helsinki-NLP/ccaligned_v1", None),
        ]
        lines = []
        total_pairs = 0
        for name, config in candidates:
            try:
                if config:
                    ds = load_dataset(name, config, split="train")
                else:
                    ds = load_dataset(name, split="train")
                # Attempt to extract parallel pairs
                for item in ds:
                    # Try common keys
                    en = item.get("translation", {}).get("en") if isinstance(item.get("translation"), dict) else item.get("en")
                    sn = None
                    if isinstance(item.get("translation"), dict):
                        sn = item.get("translation", {}).get("sn")
                    sn = sn or item.get("sn") or item.get("translation_sn")
                    if not en or not sn:
                        # Try fields like "text" for bitext corpora (simpler fallback)
                        en = en or item.get("text")
                        sn = sn or item.get("text_sn")
                    if en and sn:
                        lines.append(en.strip() + "\t" + sn.strip())
                        total_pairs += 1
                        if total_pairs % 10000 == 0:
                            write_log("INFO", "PHASE-2", f"OPUS: {total_pairs:,} pairs collected")
            except Exception as e:
                write_log("WARN", "PHASE-2", f"OPUS candidate {name} failed: {e}")
                continue
        save_text_lines(output_path, lines)
        token_est = sum(len(pair.split()) for pair in lines)
        write_log("MILESTONE", "PHASE-2", f"OPUS complete: {total_pairs:,} pairs, ~{token_est:,} tokens")
        return {"source": "opus_en_sn", "tokens": token_est, "docs": total_pairs, "path": str(output_path)}
    except Exception as e:
        write_log("ERROR", "PHASE-2", f"OPUS download failed: {e}")
        raise


def main():
    write_log("INFO", "PHASE-2", "Agent 2: scrape_data.py started")
    funcs = [
        (download_wikipedia_shona, "wikipedia_sn"),
        (download_cc100_shona, "cc100_sn"),
        (download_bible_shona, "bible_shona"),
        (download_opus_en_sn, "opus_en_sn"),
    ]
    results = []
    for fn, name in funcs:
        try:
            res = fn()
            results.append(res)
            update_manifest(res)
            # After each source, write a small checkpoint log
            write_log("MILESTONE", "PHASE-2", f"Source {name} downloaded - ~{res.get('tokens',0):,} tokens")
        except Exception as e:
            write_log("ERROR", "PHASE-2", f"Source {name} failed: {e}")
            # continue to next source
            continue

    total_tokens = sum(r.get("tokens", 0) for r in results)
    write_log("MILESTONE", "PHASE-2", f"All scraping complete. Total tokens: ~{total_tokens:,}")


if __name__ == "__main__":
    main()
