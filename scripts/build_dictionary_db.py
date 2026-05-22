"""Build an openable SQLite dictionary database from local Shona sources."""

from __future__ import annotations

import csv
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DB = ROOT / "database" / "duramazwi.db"

SOURCE_FILES = {
    "wordlist": ROOT / "data" / "dictionaries" / "shona_words.txt",
    "wiktionary": ROOT / "shona dictionary" / "wiktionary_raw.json",
    "historical": ROOT / "shona dictionary" / "historical_raw.json",
    "lexicon": ROOT / "shona dictionary" / "shona_lexicon.json",
}


@dataclass(frozen=True)
class Entry:
    word: str
    lemma: str | None
    part_of_speech: str | None
    noun_class: str | None
    definition_en: str | None
    definition_sn: str | None
    example_sentence: str | None
    source: str
    record_type: str
    synonyms_json: str | None
    antonyms_json: str | None
    raw_json: str | None


def normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def to_json(value: Any) -> str | None:
    if value in (None, "", [], {}):
        return None
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def infer_pos(entry: dict[str, Any]) -> str | None:
    return normalize_text(entry.get("part_of_speech") or entry.get("pos"))


def make_entry(
    *,
    word: Any,
    lemma: Any = None,
    part_of_speech: Any = None,
    noun_class: Any = None,
    definition_en: Any = None,
    definition_sn: Any = None,
    example_sentence: Any = None,
    source: str,
    record_type: str,
    synonyms: Any = None,
    antonyms: Any = None,
    raw: Any = None,
) -> Entry | None:
    normalized_word = normalize_text(word)
    if not normalized_word:
        return None

    return Entry(
        word=normalized_word,
        lemma=normalize_text(lemma),
        part_of_speech=normalize_text(part_of_speech),
        noun_class=normalize_text(noun_class),
        definition_en=normalize_text(definition_en),
        definition_sn=normalize_text(definition_sn),
        example_sentence=normalize_text(example_sentence),
        source=source,
        record_type=record_type,
        synonyms_json=to_json(synonyms),
        antonyms_json=to_json(antonyms),
        raw_json=to_json(raw),
    )


def load_wordlist(path: Path) -> Iterable[Entry]:
    if not path.exists():
        return []

    entries: list[Entry] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            word = line.strip()
            if not word:
                continue
            entry = make_entry(
                word=word,
                source="data/dictionaries/shona_words.txt",
                record_type="wordlist",
                raw={"word": word},
            )
            if entry:
                entries.append(entry)
    return entries


def load_json_entries(path: Path, source_name: str, record_type: str) -> Iterable[Entry]:
    if not path.exists():
        return []

    payload = load_json(path)
    if not isinstance(payload, list):
        return []

    entries: list[Entry] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        entry = make_entry(
            word=item.get("word") or item.get("lemma"),
            lemma=item.get("lemma"),
            part_of_speech=infer_pos(item),
            noun_class=item.get("class"),
            definition_en=item.get("definition_en") or item.get("gloss"),
            definition_sn=item.get("definition_sn"),
            example_sentence=item.get("example_sentence"),
            source=source_name,
            record_type=record_type,
            synonyms=item.get("synonyms"),
            antonyms=item.get("antonyms"),
            raw=item,
        )
        if entry:
            entries.append(entry)
    return entries


def iter_entries() -> list[Entry]:
    entries: list[Entry] = []
    entries.extend(load_wordlist(SOURCE_FILES["wordlist"]))
    entries.extend(load_json_entries(SOURCE_FILES["wiktionary"], "shona dictionary/wiktionary_raw.json", "wiktionary"))
    entries.extend(load_json_entries(SOURCE_FILES["historical"], "shona dictionary/historical_raw.json", "historical"))
    entries.extend(load_json_entries(SOURCE_FILES["lexicon"], "shona dictionary/shona_lexicon.json", "lexicon"))
    return entries


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA journal_mode = WAL;
        PRAGMA synchronous = NORMAL;

        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            lemma TEXT,
            part_of_speech TEXT,
            noun_class TEXT,
            definition_en TEXT,
            definition_sn TEXT,
            example_sentence TEXT,
            source TEXT NOT NULL,
            record_type TEXT NOT NULL,
            synonyms_json TEXT,
            antonyms_json TEXT,
            raw_json TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_entries_word ON entries(word);
        CREATE INDEX IF NOT EXISTS idx_entries_lemma ON entries(lemma);
        CREATE INDEX IF NOT EXISTS idx_entries_source ON entries(source);
        """
    )


def seed_metadata(connection: sqlite3.Connection, total_entries: int) -> None:
    metadata = {
        "database_name": "duramazwi.db",
        "created_by": "scripts/build_dictionary_db.py",
        "source_wordlist": str(SOURCE_FILES["wordlist"].relative_to(ROOT)),
        "source_wiktionary": str(SOURCE_FILES["wiktionary"].relative_to(ROOT)),
        "source_historical": str(SOURCE_FILES["historical"].relative_to(ROOT)),
        "source_lexicon": str(SOURCE_FILES["lexicon"].relative_to(ROOT)),
        "entry_count": str(total_entries),
    }
    connection.executemany(
        "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
        list(metadata.items()),
    )


def build_database(output_path: Path = OUTPUT_DB) -> tuple[int, int]:
    entries = iter_entries()
    unique_rows: dict[tuple[str, str, str, str, str, str], Entry] = {}

    for entry in entries:
        key = (
            entry.word.casefold(),
            (entry.lemma or "").casefold(),
            (entry.part_of_speech or "").casefold(),
            (entry.definition_en or "").casefold(),
            (entry.definition_sn or "").casefold(),
            entry.record_type.casefold(),
        )
        unique_rows[key] = entry

    rows = list(unique_rows.values())

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        try:
            output_path.unlink()
        except PermissionError:
            alt = output_path.with_name(output_path.stem + "_rebuild" + output_path.suffix)
            print(f"Warning: could not remove {output_path}; writing to {alt} instead")
            output_path = alt

    with sqlite3.connect(output_path) as connection:
        create_schema(connection)
        connection.executemany(
            """
            INSERT INTO entries(
                word, lemma, part_of_speech, noun_class,
                definition_en, definition_sn, example_sentence,
                source, record_type, synonyms_json, antonyms_json, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row.word,
                    row.lemma,
                    row.part_of_speech,
                    row.noun_class,
                    row.definition_en,
                    row.definition_sn,
                    row.example_sentence,
                    row.source,
                    row.record_type,
                    row.synonyms_json,
                    row.antonyms_json,
                    row.raw_json,
                )
                for row in rows
            ],
        )
        seed_metadata(connection, len(rows))
        connection.execute("ANALYZE")
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"integrity_check failed: {integrity}")

    return len(entries), len(rows)


def main() -> None:
    loaded, written = build_database()
    print(f"Loaded {loaded} raw records")
    print(f"Wrote {written} unique rows to {OUTPUT_DB}")


if __name__ == "__main__":
    main()
