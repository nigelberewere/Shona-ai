# SHONA AI — DATA SOURCES GUIDE
## Reference document for all agents working on Phase 2 (Data Collection)

---

## Priority Tier 1 — High Quality, High Volume

### 1. Wikipedia Shona (sn.wikipedia.org)
- **URL:** `https://dumps.wikimedia.org/snwiki/latest/snwiki-latest-pages-articles.xml.bz2`
- **HuggingFace mirror:** `wikipedia` dataset, language=`sn`
- **Est. size:** ~18,000 articles, ~2–3M tokens
- **Quality:** High — encyclopedic, edited text
- **License:** CC BY-SA 3.0
- **Download method:**
  ```python
  from datasets import load_dataset
  ds = load_dataset("wikipedia", "20231101.sn", trust_remote_code=True)
  ```

### 2. CC-100 Shona
- **HuggingFace:** `cc100`, language=`sn`
- **Est. size:** ~50–100M tokens (raw), quality varies
- **Quality:** Medium — web-crawled, needs heavy filtering
- **License:** Common Crawl terms
- **Download method:**
  ```python
  from datasets import load_dataset
  ds = load_dataset("cc100", lang="sn", streaming=True)
  ```

### 3. Shona Bible (ChiShona Bible)
- **Primary URL:** `https://raw.githubusercontent.com/christos-c/bible-corpus/master/bibles/Shona.xml`
- **Backup URL:** `https://ebible.org/Scriptures/sna_repost.zip`
- **Est. size:** ~800K tokens
- **Quality:** Very high — professionally translated, consistent style
- **License:** Public domain (1949 translation) / verify per version
- **Note:** Excellent for teaching sentence structure and Shona grammar

### 4. OPUS Parallel Corpora
- **JW300 (Shona-English):**
  ```python
  from datasets import load_dataset
  ds = load_dataset("opus_books", lang1="en", lang2="sn")
  # Also try: Helsinki-NLP/opus-100 with "en-sn"
  ```
- **CCAligned:**
  ```python
  ds = load_dataset("Helsinki-NLP/ccaligned_v1", lang1="en", lang2="sn")
  ```
- **WikiMatrix:**
  ```python
  ds = load_dataset("Helsinki-NLP/wiki_matrix", lang1="en", lang2="sn")
  ```
- **Est. size:** 100K–500K sentence pairs combined
- **Quality:** High for parallel data, good for learning Shona semantics

---

## Priority Tier 2 — Medium Quality, Supplementary

### 5. mC4 Shona
- **HuggingFace:** `mc4`, language=`sn`
- **Est. size:** varies
- **Quality:** Medium — web crawl, better filtered than CC-100
  ```python
  ds = load_dataset("mc4", "sn", streaming=True)
  ```

### 6. GlobalVoices Shona
- **URL:** `https://opus.nlpl.eu/GlobalVoices.php`
- **Est. size:** ~50K tokens
- **Quality:** High — journalism content

### 7. AfriSenti Shona (if available)
- **HuggingFace:** Search `afrisenti` for sn subset
- **Use:** Sentiment analysis benchmark data

### 8. FLORES-200 Shona
- **HuggingFace:** `facebook/flores`, language=`sna_Latn`
- **Size:** ~1,000 sentences (evaluation only)
- **Use:** Use for EVAL SET ONLY — do not train on this

---

## Priority Tier 3 — Scraping Targets

### 9. The Herald Zimbabwe (herald.co.zw)
- **URL:** `https://www.herald.co.zw`
- **Content:** Some Shona news articles
- **Method:** Scrapy spider with language detection
- **Robots.txt:** Check before scraping
- **Rate limit:** 1 request per 2 seconds

### 10. NewsDay Zimbabwe
- **URL:** `https://www.newsday.co.zw`
- **Content:** Occasional Shona content
- **Method:** Same as Herald

### 11. Radio Zimbabwe transcripts / ZBCTV
- **URL:** `https://www.zbctv.co.zw`
- **Content:** Shona broadcast content
- **Method:** Manual collection if needed

### 12. Facebook Public Groups (Manual collection)
- Shona language learning groups
- Zimbabwe community groups
- **Note:** Manual export only — respect ToS and privacy

---

## Data Collection Script Template

```python
# scripts/scrape_data.py
import logging
import json
import os
from datetime import datetime
from datasets import load_dataset
from pathlib import Path

LOG_FILE = f"logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_scrape.log"
RAW_DIR = Path("data/raw")
MANIFEST_FILE = RAW_DIR / "manifest.json"

def log(level, phase, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{level}] [{phase}] {message}"
    print(entry)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")

def download_wikipedia_shona():
    log("INFO", "PHASE-2", "Starting Wikipedia Shona download")
    try:
        ds = load_dataset("wikipedia", "20231101.sn", trust_remote_code=True)
        texts = [item["text"] for item in ds["train"]]
        output_path = RAW_DIR / "wikipedia" / "shona_wiki.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(texts))
        token_estimate = sum(len(t.split()) for t in texts)
        log("MILESTONE", "PHASE-2", 
            f"Wikipedia complete: {len(texts)} articles, ~{token_estimate:,} tokens")
        return {"source": "wikipedia_sn", "tokens": token_estimate, 
                "docs": len(texts), "path": str(output_path)}
    except Exception as e:
        log("ERROR", "PHASE-2", f"Wikipedia download failed: {e}")
        raise

def download_cc100_shona():
    log("INFO", "PHASE-2", "Starting CC-100 Shona download (streaming)")
    output_path = RAW_DIR / "cc100" / "shona_cc100.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        ds = load_dataset("cc100", lang="sn", streaming=True, split="train")
        count = 0
        token_count = 0
        with open(output_path, "w", encoding="utf-8") as f:
            for item in ds:
                text = item["text"].strip()
                if text:
                    f.write(text + "\n\n")
                    token_count += len(text.split())
                    count += 1
                if count % 10000 == 0:
                    log("INFO", "PHASE-2", f"CC-100: {count:,} docs, ~{token_count:,} tokens")
        log("MILESTONE", "PHASE-2", 
            f"CC-100 complete: {count:,} docs, ~{token_count:,} tokens")
        return {"source": "cc100_sn", "tokens": token_count, 
                "docs": count, "path": str(output_path)}
    except Exception as e:
        log("ERROR", "PHASE-2", f"CC-100 download failed: {e}")
        raise

def update_manifest(entry):
    manifest = []
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE) as f:
            manifest = json.load(f)
    manifest.append({**entry, "downloaded_at": datetime.now().isoformat()})
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)

if __name__ == "__main__":
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    results = []
    for fn in [download_wikipedia_shona, download_cc100_shona]:
        try:
            result = fn()
            results.append(result)
            update_manifest(result)
        except Exception as e:
            log("ERROR", "PHASE-2", f"Source failed, continuing: {e}")
    
    total_tokens = sum(r["tokens"] for r in results)
    log("MILESTONE", "PHASE-2", 
        f"All sources complete. Total: ~{total_tokens:,} tokens from {len(results)} sources")
```

---

## Data Quality Requirements

After collection, each source must pass:
- [ ] File exists and is non-empty
- [ ] UTF-8 encoded
- [ ] > 80% Shona content (langdetect check)
- [ ] No binary/garbage content
- [ ] Logged in `manifest.json` with token count

## Minimum Data Targets

| Tier | Token count | Action |
|------|-------------|--------|
| Bare minimum | 5M tokens | Can train v0.1 small |
| Good | 20M tokens | Can train v0.1 base |
| Excellent | 50M+ tokens | Full production training |

---

*Data Sources Guide v1.0 | Shona AI Project*
