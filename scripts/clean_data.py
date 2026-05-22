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

WORDLIST_FILE = Path("data/dictionaries/shona_words.txt")

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
    "vana",
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

# Additional common Shona/Bible/wiki words to improve lexical matching
SHONA_COMMON_WORDS.update({
    "mwana",
    "musha",
    "shoko",
    "rudo",
    "kurarama",
    "kufamba",
    "kudya",
    "ndiri",
    "uri",
    "tiri",
    "saka",
    "zita",
    "ndiani",
    "kumba",
    "chikoro",
    "munamato",
    "vakanga",
    "zvapera",
    "ndatenda",
    "mambo",
    "vapambi",
    "shiri",
    "rima",
    "mazuva",
    # Additional Bible / wiki common words
    "jesu",
    "kirisitu",
    "mweya",
    "mutumwa",
    "apostora",
    "mariya",
    "moses",
    "isaya",
    "rufu",
    "nyasha",
    "chechi",
    "baba",
    "mai",
    "hama",
    "mhuri",
    "zvakanaka",
    "tsananguro",
    "shanduro",
})

# Ultra-strict whitelist mode: allow only letters, spaces and basic punctuation
ULTRA_STRICT = True
ALLOWED_PUNCT = set(".,;:!?\'\-\"()")

STRUCTURAL_REJECT_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bclass\s*=", r"\bstyle\s*=", r"\bid\s*=", r"\bdata-\w+\s*=",
        r"\bbackground(?:-color)?\s*=", r"\bbgcolor\s*=", r"\bfg(?:color)?\s*=",
        r"\bwidth\s*=", r"\bheight\s*=", r"\bpadding\s*=", r"\bmargin\s*=",
        r"\bdisplay\s*=", r"\bbuttonlabel\s*=", r"\bvalign\s*=", r"\balign\s*=",
        r"\bcolspan\s*=", r"\browspan\s*=", r"\bfont-size\s*=", r"\bfont-weight\s*=",
        r"\bfont-family\s*=", r"\btext-align\s*=", r"\bvertical-align\s*=", r"\bborder\s*=",
        r"\bshadow\s*=", r"\bframeless\b", r"\bwikitable\b", r"\bmw-[\w-]+\b",
        r"\bwiki-?template\b", r"\bcategory\s*:", r"\bimage\s*:", r"\bfile\s*:",
        r"\bindirection\s*:", r"\bpx\b", r"\b(?:\d{1,4}x\d{1,4})px?\b",
        r"\b(?:right|left|center)\s+frameless\b", r"\bfree\s+ssr\s+peji\b",
        r"\bthis page has been nominated for speedy deletion\b", r"\brelated zvinogadzirwa\b",
        r"\bspeedy deletion\b", r"\bnominated for deletion\b", r"\brfc\d+\b", r"\bafd\b",
        r"\bmediawiki\b", r"\btemplate\b", r"\bbot log\b", r"\btranslation table\b",
        r"\bmetadata\b", r"\blog(?:ging|page)?\b", r"\b(?:edit|view)\s+history\b",
        r"\bbutton\s*label\b", r"\bnoinclude\b", r"\bincludeonly\b", r"\bonlyinclude\b",
        r"\b(?:interwiki|interlanguage)\s*link\b", r"^\s*\|.*\|\s*$", r"^\s*!.*!\s*$",
        r"'''.+?'''", r"\(\s*(?:v|n|adj|adv)\.\s+[^)]{1,30}\)", r"\(\s*(?:noun|verb|adjective|adverb)\s*\)",
        r"vanoti\s+[^\s]+\s+kureva\b", r"\b[a-z]{2,40}\s+vanoti\s+[a-z']+\s*\([^)]*\)\s*kureva\b",
            r"vanoti\s+\w+\s*\([^)]*\)\s*kureva\b",
        r"\w+-(?:sulfonyl|methyl|phenyl|hydroxyl)\b", r"\d+x\d+x\d+\s+(?:mm|cm|m|km)\b",
        r"\(\s*[a-z]{1,10}\s*:\s*[a-z]{1,10}\s*\)", r"iso\s+639|unicode\s+block", r"\bcharacteris\b",
    )
]

SYSTEM_LOG_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"^la(?:,\s*[a-z]{1,3}){2,}\b", r"^lb(?:,\s*[a-z]{1,3}){2,}\b", r"^li(?:,\s*[a-z]{1,3}){2,}\b",
        r"\bthis page has been nominated for speedy deletion\b", r"\bfree ssr peji\b", r"\brelated zvinogadzirwa\b",
        r"\bdownload\b.*\btemplate\b", r"\bvisit\b.*\bwiki\b", r"\b(?:bot|timestamp|edit|revision)\s+(?:log|record|entry)\b",
        r"\bby user:\b", r"\bat \d{2}:\d{2}", r"{{.{0,60}}}", r"\[\[.*?\|.*?\]\]", r"^\s*\[\[Category:",
        r"^\s*category\s*:", r"https?://\S+", r"\bwikipedia\b.*\blink\b", r"^\s*(?:row|col|cell|td|th|table)\s*\d+\b",
        r"latn|zyyy|zinh|zzzz", r"arameic|coptic\s+block", r"\bhebraic\b|\barabic\b.*block", r"\b--\s+and\s+",
        r"\(by force|compulsorily\)", r"hydrochloride|amine\s+hydrochloride", r"silicones\s+kuratidza",
    )
]

ENGLISH_BOILERPLATE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bapologies? for (?:writing|delivering|addressing) you in english\b",
        r"\bsorry for (?:writing|delivering|addressing) you in english\b",
        r"\bplease help translate(?: the)? pages?\b",
        r"\bplease help translate(?: it)?\b",
        r"\bplease help us by providing a translation below\b",
        r"\bwe look forward to collaborating with you\b",
        r"\bwe welcome your feedback and questions\b",
        r"\bthank you for your help and your understanding\b",
        r"\bdo you want to help attract new contributors\b",
        r"\bdo you want to improve retention of our existing editors\b",
        r"\bdo you want to strengthen our community\b",
        r"\bthe wikimedia foundation\b",
        r"\bwikimedia foundation\b",
        r"\bwikimedia projects\b",
        r"\bglobal message delivery\b",
        r"\btranslatewiki\.net\b",
        r"\bmeta-wiki\b",
        r"\bmeta wiki\b",
        r"\buser experience project\b",
        r"\bfundraising committee\b",
        r"\brequest for comment\b",
        r"\bsecurepoll voting page\b",
        r"\bthe following are the areas that you will probably be most interested in\b",
        r"\bfaster loading of javascript files\b",
        r"\bbetter timezone recognition\b",
        r"\blanguage converter improved\b",
        r"\bthe project is divided into three phases\b",
        r"\blanguage links in the sidebar\b",
        r"\bthis extension is designed to help organizers\b",
        r"\bthe three main features of this extension are\b",
        r"\bwe invite you to take part\b",
    )
]

DICTIONARY_ENTRY_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"^\s*[a-zàáâãäāăąǎǻ]{2,80}\s*\([^\)]{1,80}\)\s*;\s*(?:to|for|meaning|denotes|means|synonym)",
        r"^\s*[a-zàáâãäāăąǎǻ]{2,80}\s*:\s*(?:n\.|v\.|adj\.|adv\.|noun|verb|adjective|adverb)\b",
        r"^\s*[a-zàáâãäāăąǎǻ]{2,80}\s*=\s*[a-zàáâãäāăąǎǻ\s]{2,80}$", r"\b(?:dictionary|gloss|lemma|entry|headword|sense)\b",
        r"\b(?:translation|equivalent|means?|synonyms?|antonyms?)\s+to\b", r"^\s*[a-zàáâãäāăąǎǻ]{1,40}\s*;\s*[a-z]{1,40}\s*;\s*[a-z]{1,40}\s*$",
        r"^\s*(?:sn|en|fr|pt|es|sw|zu|xh|ny)\s*[,/]\s*(?:sn|en|fr|pt|es|sw|zu|xh|ny)",
    )
]


def is_structural_contamination(text: str) -> bool:
    if not text or len(text.strip()) < 10:
        return True
    lower_text = text.casefold()
    if any(pattern.search(lower_text) for pattern in STRUCTURAL_REJECT_PATTERNS):
        return True
    if any(pattern.search(lower_text) for pattern in SYSTEM_LOG_PATTERNS):
        return True
    if any(pattern.search(lower_text) for pattern in ENGLISH_BOILERPLATE_PATTERNS):
        return True
    # Reject bare layout fragments or high token repetition
    token_count = len(text.split())
    if token_count <= 3 and any(marker in lower_text for marker in ["px", "frameless", "right", "left", "|", "="]):
        return True
    # Reject lines mostly non-alphabetic (URLs, hex codes, etc.)
    alpha_ratio = sum(c.isalpha() for c in text) / max(len(text), 1)
    if alpha_ratio < 0.45:
        return True
    # Ultra-strict whitelist: allow only alphabetic, spaces and a small set of punctuation
    if ULTRA_STRICT:
        for c in text:
            if not (c.isalpha() or c.isspace() or c in ALLOWED_PUNCT):
                return True
        # Require higher alphabetic density in ultra-strict mode
        if alpha_ratio < 0.70:
            return True
    # Reject repetitive patterns (sign of junk data)
    if token_count >= 4:
        tokens = text.split()
        most_common = max(set(tokens), key=tokens.count)
        if tokens.count(most_common) >= token_count * 0.5:
            return True
    return False


def is_dictionary_entry_like(text: str) -> bool:
    """Identify lines that are dictionary entries, lemmas, or glosses rather than natural prose."""
    lower_text = text.casefold().strip()
    if len(lower_text) < 12:
        return True
    token_count = len(lower_text.split())
    sentence_marks = sum(lower_text.count(mark) for mark in ".?!")
    # Check dictionary patterns; longer natural text may mention glosses
    if any(pattern.search(lower_text) for pattern in DICTIONARY_ENTRY_PATTERNS):
        if token_count < 20 or sentence_marks == 0:
            return True
    # Reject structured gloss patterns
    if "; to " in lower_text or "; for " in lower_text or "; meaning " in lower_text:
        if token_count < 25 and lower_text.count(";") >= 1:
            return True
    # Reject short lines with colon gloss patterns (POS markers)
    if ":" in lower_text and token_count <= 10:
        if any(pos in lower_text for pos in [" n. ", " v. ", " adj. ", " adv. ", "(noun)", "(verb)", "(adj)"]):
            return True
    # Reject glosses with POS markers in parentheses anywhere in the line
    gloss_patterns = [
        r"\(\s*v\.\s+[^)]{1,30}\)", r"\(\s*n\.\s+[^)]{1,30}\)",
        r"\(\s*adj\.\s+[^)]{1,30}\)", r"\(\s*adv\.\s+[^)]{1,30}\)",
    ]
    if any(re.search(pat, lower_text, re.IGNORECASE) for pat in gloss_patterns):
        if token_count < 25:
            return True

    # Reject parentheses containing semicolons or English gloss tokens
    paren_matches = re.findall(r"\(([^)]{1,120})\)", text)
    for inner in paren_matches:
        inner_l = inner.lower()
        if ";" in inner_l:
            if token_count < 40:
                return True
        # common English/function words inside parentheses (sign of gloss/translation)
        if re.search(r"\b(one|ones|the|and|or|to|of|in|bees|bee|noun|verb|means|meaning|details|detail)\b", inner_l):
            if token_count < 40:
                return True

    # Reject lines with "vanoti ... kureva" dictionary pattern (more aggressive)
    if "vanoti" in lower_text and "kureva" in lower_text:
        if token_count < 40:
            return True
    return False


def has_sentence_shape(text: str) -> bool:
    token_count = len(text.split())
    if token_count < 5:
        return False
    alpha_ratio = sum(char.isalpha() for char in text) / max(len(text), 1)
    # Text with terminal punctuation and decent alphabetic content
    if any(mark in text for mark in (".", "?", "!")):
        return alpha_ratio >= 0.60
    # Colons and semicolons OK if they structure clauses (sufficient alphabetic content)
    if any(mark in text for mark in (";", ":")):
        return token_count >= 8 and alpha_ratio >= 0.62
    # Prose without punctuation but long and lexically dense
    return token_count >= 12 and alpha_ratio >= 0.68

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
    tokens = re.findall(r"[^\W\d_]+", text.casefold(), flags=re.UNICODE)
    if not tokens:
        return 0
    dictionary_words = load_shona_dictionary()
    return sum(1 for token in tokens if token in dictionary_words)


@lru_cache(maxsize=1)
def load_shona_dictionary() -> set[str]:
    words = {normalize_word(word) for word in SHONA_COMMON_WORDS}
    if WORDLIST_FILE.exists():
        with open(WORDLIST_FILE, "r", encoding="utf-8") as handle:
            for line in handle:
                word = normalize_word(line)
                if word:
                    words.add(word.casefold())
    return {word.casefold() for word in words}


def normalize_word(word: str) -> str:
    return unicodedata.normalize("NFC", word).strip()


def shona_lexical_support(text: str) -> tuple[int, float]:
    tokens = re.findall(r"[^\W\d_]+", text.casefold(), flags=re.UNICODE)
    if not tokens:
        return 0, 0.0
    hits = shona_lexical_score(text)
    return hits, hits / len(tokens)


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
    hits, hit_ratio = shona_lexical_support(text)
    if hits >= 2 or hit_ratio >= 0.15:
        return True
    if not looks_like_shona(text):
        return False
    return detect_shona_probability(text) >= 0.05


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
    if is_structural_contamination(text):
        return ""
    if is_dictionary_entry_like(text):
        return ""
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
        if not has_sentence_shape(cleaned):
            removed_junk += 1
            continue
        # Source-specific language filtering rules:
        # - bible_shona: trusted source — skip langdetect and keep cleaned lines
        # - opus_en_sn: parallel file — we already extracted the Shona column, skip langdetect
        # - wikipedia_sn: relax langdetect threshold to 0.05 OR accept if any Shona hint/lexical match
        if spec.name == "bible_shona" or spec.name == "opus_en_sn":
            pass
        elif spec.name == "wikipedia_sn":
            has_hint = any(f" {hint} " in f" {cleaned.casefold()} " for hint in SHONA_HINTS)
            hits, hit_ratio = shona_lexical_support(cleaned)
            alpha_ratio = sum(char.isalpha() for char in cleaned) / max(len(cleaned), 1)
            if hits >= 1 or hit_ratio >= 0.025 or has_hint or (len(cleaned) >= 12 and cleaned.count(" ") >= 1 and alpha_ratio >= 0.47):
                pass
            else:
                removed_language += 1
                continue
        else:
            if not is_probably_shona(cleaned):
                removed_language += 1
                continue
        normalized_key = cleaned.casefold()
        if spec.name == "wikipedia_sn":
            if normalized_key in global_seen:
                removed_duplicates += 1
                continue
            global_seen.add(normalized_key)
        elif spec.name == "opus_en_sn":
            pass
        else:
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
                handle.write(f"{line} </s>\n")
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
            handle.write(f"{line} </s>\n")
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
