import bz2
import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import requests
from datasets import load_dataset


NOW = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / f"{NOW}_agent2.log"

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_FILE = RAW_DIR / "manifest.json"


def write_log(level, phase, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{level}] [{phase}] {message}"
    print(entry)
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(entry + "\n")


def update_manifest(entry: dict):
    manifest = []
    if MANIFEST_FILE.exists():
        try:
            with open(MANIFEST_FILE, "r", encoding="utf-8") as handle:
                manifest = json.load(handle)
        except Exception:
            manifest = []
    manifest.append({**entry, "downloaded_at": datetime.now().isoformat()})
    with open(MANIFEST_FILE, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
    write_log("MILESTONE", "PHASE-2", f"Manifest updated for {entry.get('source')}")


def save_text_lines(path: Path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for line in lines:
            handle.write(line.replace("\r", "") + "\n")


def count_tokens_in_lines(lines):
    return sum(len(line.split()) for line in lines)


def extract_wiki_articles_from_dump(xml_stream):
    namespace_pattern = re.compile(r"\{.*\}")
    texts = []
    for _, elem in ET.iterparse(xml_stream, events=("end",)):
        tag = namespace_pattern.sub("", elem.tag).lower()
        if tag == "text":
            text = (elem.text or "").strip()
            if text:
                texts.append(text)
        elem.clear()
    return texts


def download_wikipedia_shona():
    output_path = RAW_DIR / "wikipedia" / "shona_wiki.txt"
    write_log("INFO", "PHASE-2", "Starting Wikipedia Shona download via datasets")
    try:
        dataset = load_dataset("wikipedia", "20231101.sn", split="train", trust_remote_code=True)
        texts = [item["text"].strip() for item in dataset if item.get("text")]
        save_text_lines(output_path, texts)
        token_estimate = count_tokens_in_lines(texts)
        result = {"source": "wikipedia_sn", "tokens": token_estimate, "docs": len(texts), "path": str(output_path)}
        write_log("MILESTONE", "PHASE-2", f"Wikipedia complete: {len(texts)} articles, ~{token_estimate:,} tokens")
        return result
    except Exception as error:
        write_log("WARN", "PHASE-2", f"Wikipedia dataset path failed, using Wikimedia dump fallback: {error}")
        dump_url = "https://dumps.wikimedia.org/snwiki/latest/snwiki-latest-pages-articles.xml.bz2"
        dump_path = RAW_DIR / "wikipedia" / "snwiki-latest-pages-articles.xml.bz2"
        dump_path.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(dump_url, stream=True, timeout=300) as response:
            response.raise_for_status()
            with open(dump_path, "wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
        with bz2.open(dump_path, "rb") as compressed:
            xml_bytes = compressed.read()
        texts = extract_wiki_articles_from_dump(io.BytesIO(xml_bytes))
        if not texts:
            decoded = bz2.open(dump_path, "rb").read().decode("utf-8", errors="ignore")
            texts = [line.strip() for line in decoded.splitlines() if line.strip()]
        save_text_lines(output_path, texts)
        token_estimate = count_tokens_in_lines(texts)
        result = {
            "source": "wikipedia_sn",
            "tokens": token_estimate,
            "docs": len(texts),
            "path": str(output_path),
            "fallback": "wikimedia_dump",
        }
        write_log("MILESTONE", "PHASE-2", f"Wikipedia fallback complete: {len(texts)} lines, ~{token_estimate:,} tokens")
        return result


def download_cc100_shona():
    output_path = RAW_DIR / "cc100" / "shona_cc100.txt"
    write_log("INFO", "PHASE-2", "Starting CC-100 Shona download (streaming)")
    try:
        dataset = load_dataset("cc100", lang="sn", split="train", streaming=True, trust_remote_code=True)
        lines = []
        count = 0
        token_count = 0
        for item in dataset:
            text = item.get("text") if isinstance(item, dict) else str(item)
            text = (text or "").strip()
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
    except Exception as error:
        write_log("WARN", "PHASE-2", f"CC-100 unavailable, trying mc4/sn fallback: {error}")
        dataset = load_dataset("mc4", "sn", streaming=True, trust_remote_code=True)
        lines = []
        count = 0
        token_count = 0
        for item in dataset:
            if isinstance(item, str):
                text = item.strip()
            else:
                text = (item.get("text") or item.get("content") or "").strip()
            if not text:
                continue
            lines.append(text)
            token_count += len(text.split())
            count += 1
            if count % 10000 == 0:
                write_log("INFO", "PHASE-2", f"mc4/sn: {count:,} docs, ~{token_count:,} tokens")
        save_text_lines(output_path, lines)
        write_log("MILESTONE", "PHASE-2", f"mc4/sn fallback complete: {count:,} docs, ~{token_count:,} tokens")
        return {"source": "cc100_sn", "tokens": token_count, "docs": count, "path": str(output_path), "fallback": "mc4/sn"}


def download_bible_shona():
    output_path = RAW_DIR / "bible" / "shona_bible.txt"
    write_log("INFO", "PHASE-2", "Starting Shona Bible download from GitHub raw")
    url = "https://raw.githubusercontent.com/christos-c/bible-corpus/master/bibles/Shona.xml"
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    content = response.content
    try:
        root = ET.fromstring(content)
        verses = []
        for elem in root.iter():
            if elem.tag.lower().endswith("verse") or elem.tag.lower().endswith("text"):
                text = (elem.text or "").strip()
                if text:
                    verses.append(text)
        if not verses:
            verses = [line.strip() for line in content.decode("utf-8", errors="ignore").splitlines() if line.strip()]
    except Exception:
        verses = [line.strip() for line in content.decode("utf-8", errors="ignore").splitlines() if line.strip()]
    save_text_lines(output_path, verses)
    token_estimate = count_tokens_in_lines(verses)
    write_log("MILESTONE", "PHASE-2", f"Bible download complete: ~{token_estimate:,} tokens, {len(verses)} lines")
    return {"source": "bible_shona", "tokens": token_estimate, "docs": len(verses), "path": str(output_path)}


def download_opus_en_sn():
    output_path = RAW_DIR / "opus" / "en-sn_parallel.txt"
    write_log("INFO", "PHASE-2", "Starting OPUS parallel (en-sn) download via datasets")
    lines = []
    total_pairs = 0
    candidates = [
        ("Helsinki-NLP/opus-100", "en-sn"),
        ("Helsinki-NLP/wiki_matrix", "en-sn"),
        ("Helsinki-NLP/ccaligned_v1", "en-sn"),
        ("opus_books", None),
    ]
    for name, config in candidates:
        try:
            if config:
                dataset = load_dataset(name, config, split="train")
            else:
                dataset = load_dataset(name, split="train")
            for item in dataset:
                translation = item.get("translation") if isinstance(item, dict) else None
                en = translation.get("en") if isinstance(translation, dict) else item.get("en") if isinstance(item, dict) else None
                sn = translation.get("sn") if isinstance(translation, dict) else item.get("sn") if isinstance(item, dict) else None
                if not en or not sn:
                    en = en or (item.get("text") if isinstance(item, dict) else None)
                    sn = sn or (item.get("text_sn") if isinstance(item, dict) else None)
                if en and sn:
                    lines.append(en.strip() + "\t" + sn.strip())
                    total_pairs += 1
                    if total_pairs % 10000 == 0:
                        write_log("INFO", "PHASE-2", f"OPUS: {total_pairs:,} pairs collected")
        except Exception as error:
            write_log("WARN", "PHASE-2", f"OPUS candidate {name} failed: {error}")
            continue

    if total_pairs == 0:
        write_log("INFO", "PHASE-2", "Trying direct OPUS CCAligned zip fallback")
        zip_url = "https://object.pouta.csc.fi/OPUS-CCAligned/v1/moses/en-sn.txt.zip"
        response = requests.get(zip_url, timeout=300)
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            en_name = next((name for name in archive.namelist() if name.endswith(".en")), None)
            sn_name = next((name for name in archive.namelist() if name.endswith(".sn")), None)
            if not en_name or not sn_name:
                raise RuntimeError(f"Unexpected OPUS zip contents: {archive.namelist()}")
            en_lines = archive.read(en_name).decode("utf-8", errors="ignore").splitlines()
            sn_lines = archive.read(sn_name).decode("utf-8", errors="ignore").splitlines()
            pair_count = min(len(en_lines), len(sn_lines))
            for index in range(pair_count):
                en = en_lines[index].strip()
                sn = sn_lines[index].strip()
                if en and sn:
                    lines.append(en + "\t" + sn)
                    total_pairs += 1
            write_log("MILESTONE", "PHASE-2", f"OPUS CCAligned fallback complete: {total_pairs:,} pairs")

    save_text_lines(output_path, lines)
    token_estimate = sum(len(pair.split()) for pair in lines)
    write_log("MILESTONE", "PHASE-2", f"OPUS complete: {total_pairs:,} pairs, ~{token_estimate:,} tokens")
    return {"source": "opus_en_sn", "tokens": token_estimate, "docs": total_pairs, "path": str(output_path)}


def main():
    write_log("INFO", "PHASE-2", "Agent 2: scrape_data.py started")
    sources = [
        (download_wikipedia_shona, "wikipedia_sn"),
        (download_cc100_shona, "cc100_sn"),
        (download_bible_shona, "bible_shona"),
        (download_opus_en_sn, "opus_en_sn"),
    ]
    results = []
    for fn, name in sources:
        try:
            result = fn()
            results.append(result)
            update_manifest(result)
            write_log("MILESTONE", "PHASE-2", f"Source {name} downloaded - ~{result.get('tokens', 0):,} tokens")
        except Exception as error:
            write_log("ERROR", "PHASE-2", f"Source {name} failed: {error}")

    total_tokens = sum(item.get("tokens", 0) for item in results)
    write_log("MILESTONE", "PHASE-2", f"All scraping complete. Total tokens: ~{total_tokens:,}")


if __name__ == "__main__":
    main()