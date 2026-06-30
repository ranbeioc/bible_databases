#!/usr/bin/env python3
"""Import Arabic Smith & Van Dyck from BibleAquifer JSON into local formats."""

from __future__ import annotations

import csv
import html
import json
import re
import sqlite3
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_REPO = "BibleAquifer/ArabicVanDyckBible"
SOURCE_BRANCH = "main"
SOURCE_DIR = "arb/json"
SOURCE_TREE_URL = f"https://github.com/{SOURCE_REPO}/tree/{SOURCE_BRANCH}/{SOURCE_DIR}"
RAW_BASE_URL = f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_BRANCH}/{SOURCE_DIR}"
COMMIT_API_URL = f"https://api.github.com/repos/{SOURCE_REPO}/commits/{SOURCE_BRANCH}"

LANG = "ar"
LANGUAGE_TAG = "arb"
VERSION = "SVD"
NAME = "Arabic Smith & Van Dyck"
NATIVE_NAME = "الفاندايك"
DIRECTION = "rtl"
TRANSLATION_TITLE = f"{VERSION}: {NAME}"
LICENSE_LABEL = "Public Domain / CC0 per BibleAquifer ArabicVanDyckBible"

CANONICAL_BOOKS: list[tuple[int, str]] = [
    (1, "Genesis"),
    (2, "Exodus"),
    (3, "Leviticus"),
    (4, "Numbers"),
    (5, "Deuteronomy"),
    (6, "Joshua"),
    (7, "Judges"),
    (8, "Ruth"),
    (9, "I Samuel"),
    (10, "II Samuel"),
    (11, "I Kings"),
    (12, "II Kings"),
    (13, "I Chronicles"),
    (14, "II Chronicles"),
    (15, "Ezra"),
    (16, "Nehemiah"),
    (17, "Esther"),
    (18, "Job"),
    (19, "Psalms"),
    (20, "Proverbs"),
    (21, "Ecclesiastes"),
    (22, "Song of Solomon"),
    (23, "Isaiah"),
    (24, "Jeremiah"),
    (25, "Lamentations"),
    (26, "Ezekiel"),
    (27, "Daniel"),
    (28, "Hosea"),
    (29, "Joel"),
    (30, "Amos"),
    (31, "Obadiah"),
    (32, "Jonah"),
    (33, "Micah"),
    (34, "Nahum"),
    (35, "Habakkuk"),
    (36, "Zephaniah"),
    (37, "Haggai"),
    (38, "Zechariah"),
    (39, "Malachi"),
    (40, "Matthew"),
    (41, "Mark"),
    (42, "Luke"),
    (43, "John"),
    (44, "Acts"),
    (45, "Romans"),
    (46, "I Corinthians"),
    (47, "II Corinthians"),
    (48, "Galatians"),
    (49, "Ephesians"),
    (50, "Philippians"),
    (51, "Colossians"),
    (52, "I Thessalonians"),
    (53, "II Thessalonians"),
    (54, "I Timothy"),
    (55, "II Timothy"),
    (56, "Titus"),
    (57, "Philemon"),
    (58, "Hebrews"),
    (59, "James"),
    (60, "I Peter"),
    (61, "II Peter"),
    (62, "I John"),
    (63, "II John"),
    (64, "III John"),
    (65, "Jude"),
    (66, "Revelation of John"),
]


def request_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "xhalo-bible-importer"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_source_commit() -> str:
    data = request_json(COMMIT_API_URL)
    sha = data.get("sha")
    if not isinstance(sha, str) or len(sha) < 12:
        raise RuntimeError("Could not resolve source commit SHA")
    return sha


def fetch_book_records(book_number: int) -> list[dict[str, Any]]:
    url = f"{RAW_BASE_URL}/{book_number:02d}.content.json"
    records = request_json(url)
    if not isinstance(records, list):
        raise RuntimeError(f"Unexpected source payload for {book_number:02d}.content.json")
    return records


def clean_text(raw: str) -> str:
    text = re.sub(r"<sup\b[^>]*>.*?</sup>", " ", raw, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text, flags=re.UNICODE)
    return text.strip()


def build_corpus() -> tuple[dict[str, Any], dict[str, Any]]:
    source_commit = fetch_source_commit()
    books: list[dict[str, Any]] = []
    verse_count = 0
    empty_count = 0
    raw_record_count = 0
    samples: dict[str, str] = {}

    for expected_book_number, book_name in CANONICAL_BOOKS:
        chapters: dict[int, dict[int, str]] = defaultdict(dict)
        for record in fetch_book_records(expected_book_number):
            raw_record_count += 1
            index_reference = str(record.get("index_reference", ""))
            if not re.fullmatch(r"\d{8}", index_reference):
                raise RuntimeError(f"Invalid index_reference: {index_reference!r}")
            book_number = int(index_reference[0:2])
            chapter_number = int(index_reference[2:5])
            verse_number = int(index_reference[5:8])
            if book_number != expected_book_number:
                raise RuntimeError(
                    f"Book mismatch in {expected_book_number:02d}.content.json: {index_reference}"
                )
            if record.get("language") != LANGUAGE_TAG:
                raise RuntimeError(f"Unexpected source language for {index_reference}: {record.get('language')!r}")
            text = clean_text(str(record.get("content", "")))
            if not text:
                empty_count += 1
                continue
            chapters[chapter_number][verse_number] = text
            verse_count += 1
            if expected_book_number == 1 and chapter_number == 1 and verse_number == 1:
                samples["Genesis 1:1"] = text
            if expected_book_number == 43 and chapter_number == 3 and verse_number == 16:
                samples["John 3:16"] = text

        book_payload = {
            "name": book_name,
            "chapters": [
                {
                    "chapter": chapter_number,
                    "verses": [
                        {"verse": verse_number, "text": verses[verse_number]}
                        for verse_number in sorted(verses)
                    ],
                }
                for chapter_number, verses in sorted(chapters.items())
            ],
        }
        if not book_payload["chapters"]:
            raise RuntimeError(f"No chapters imported for {book_name}")
        books.append(book_payload)

    if len(books) != 66:
        raise RuntimeError(f"Expected 66 books, imported {len(books)}")
    if empty_count:
        raise RuntimeError(f"Source import produced {empty_count} empty verses")
    for sample_ref in ("Genesis 1:1", "John 3:16"):
        if sample_ref not in samples:
            raise RuntimeError(f"Missing required sample: {sample_ref}")

    corpus = {"translation": TRANSLATION_TITLE, "books": books}
    audit = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "repo": SOURCE_REPO,
            "tree_url": SOURCE_TREE_URL,
            "commit": source_commit,
            "path": SOURCE_DIR,
            "license": LICENSE_LABEL,
        },
        "metadata": {
            "lang": LANG,
            "languageTag": LANGUAGE_TAG,
            "version": VERSION,
            "name": NAME,
            "nativeName": NATIVE_NAME,
            "direction": DIRECTION,
        },
        "counts": {
            "source_files": 66,
            "source_records": raw_record_count,
            "books": len(books),
            "chapters": sum(len(book["chapters"]) for book in books),
            "verses": verse_count,
            "empty_verses": empty_count,
        },
        "samples": samples,
    }
    return corpus, audit


def ensure_output_dirs() -> None:
    for name in ("csv", "json", "yaml", "sql", "md", "txt", "sqlite"):
        (ROOT / "formats" / name).mkdir(parents=True, exist_ok=True)
    (ROOT / "reports").mkdir(parents=True, exist_ok=True)


def write_json(corpus: dict[str, Any]) -> None:
    path = ROOT / "formats" / "json" / f"{VERSION}.json"
    path.write_text(json.dumps(corpus, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")


def iter_verses(corpus: dict[str, Any]):
    for book_index, book in enumerate(corpus["books"], start=1):
        for chapter in book["chapters"]:
            for verse in chapter["verses"]:
                yield book_index, book["name"], int(chapter["chapter"]), int(verse["verse"]), verse["text"]


def write_csv(corpus: dict[str, Any]) -> None:
    with (ROOT / "formats" / "csv" / f"{VERSION}.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        for _, book_name, chapter, verse, text in iter_verses(corpus):
            writer.writerow([book_name, chapter, verse, text])


def write_yaml(corpus: dict[str, Any]) -> None:
    # JSON is valid YAML 1.2 and avoids introducing a PyYAML dependency.
    path = ROOT / "formats" / "yaml" / f"{VERSION}.yaml"
    path.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_markdown(corpus: dict[str, Any]) -> None:
    lines = [f"# {TRANSLATION_TITLE}", ""]
    for book in corpus["books"]:
        lines.extend([f"## {book['name']}", ""])
        for chapter in book["chapters"]:
            lines.extend([f"### Chapter {chapter['chapter']}", ""])
            for verse in chapter["verses"]:
                lines.extend([f"**[{chapter['chapter']}:{verse['verse']}]** {verse['text']}", ""])
    (ROOT / "formats" / "md" / f"{VERSION}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_text(corpus: dict[str, Any]) -> None:
    lines: list[str] = []
    for book in corpus["books"]:
        lines.extend([f"### {book['name']}", ""])
        for chapter in book["chapters"]:
            for verse in chapter["verses"]:
                lines.append(f"[{chapter['chapter']}:{verse['verse']}] {verse['text']}")
        lines.append("")
    (ROOT / "formats" / "txt" / f"{VERSION}.txt").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def sql_quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def write_sql(corpus: dict[str, Any]) -> None:
    lines = [
        f"-- SQL Dump for # {TRANSLATION_TITLE} ({VERSION})",
        f"-- License: {LICENSE_LABEL}",
        "",
        f"DROP TABLE IF EXISTS `{VERSION}_books`;",
        f"DROP TABLE IF EXISTS `{VERSION}_verses`;",
        "DROP TABLE IF EXISTS `translations`;",
        "",
        "CREATE TABLE IF NOT EXISTS `translations` (",
        "  `translation` VARCHAR(255) PRIMARY KEY,",
        "  `title` VARCHAR(255),",
        "  `license` TEXT",
        ");",
        "",
        "INSERT INTO `translations` (`translation`, `title`, `license`) VALUES "
        f"({sql_quote(VERSION)}, {sql_quote('# ' + TRANSLATION_TITLE)}, {sql_quote(LICENSE_LABEL)});",
        "",
        f"CREATE TABLE `{VERSION}_books` (",
        "  `id` INT AUTO_INCREMENT PRIMARY KEY,",
        "  `name` VARCHAR(255)",
        ");",
    ]
    for _, book_name in CANONICAL_BOOKS:
        lines.append(f"INSERT INTO `{VERSION}_books` (`name`) VALUES ({sql_quote(book_name)});")
    lines.extend(
        [
            "",
            f"CREATE TABLE `{VERSION}_verses` (",
            "  `book_id` INT,",
            "  `chapter` INT,",
            "  `verse` INT,",
            "  `text` TEXT",
            ");",
        ]
    )
    for book_id, _, chapter, verse, text in iter_verses(corpus):
        lines.append(
            f"INSERT INTO `{VERSION}_verses` (`book_id`, `chapter`, `verse`, `text`) "
            f"VALUES ({book_id}, {chapter}, {verse}, {sql_quote(text)});"
        )
    (ROOT / "formats" / "sql" / f"{VERSION}.sql").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_sqlite(corpus: dict[str, Any]) -> None:
    path = ROOT / "formats" / "sqlite" / f"{VERSION}.db"
    if path.exists():
        path.unlink()
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE translations (translation TEXT PRIMARY KEY, title TEXT, license TEXT)")
        connection.execute(
            "INSERT INTO translations (translation, title, license) VALUES (?, ?, ?)",
            (VERSION, f"# {TRANSLATION_TITLE}", LICENSE_LABEL),
        )
        connection.execute(f"CREATE TABLE {VERSION}_books (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
        connection.execute(f"CREATE TABLE {VERSION}_verses (book_id INTEGER, chapter INTEGER, verse INTEGER, text TEXT)")
        for _, book_name in CANONICAL_BOOKS:
            connection.execute(f"INSERT INTO {VERSION}_books (name) VALUES (?)", (book_name,))
        connection.executemany(
            f"INSERT INTO {VERSION}_verses (book_id, chapter, verse, text) VALUES (?, ?, ?, ?)",
            ((book_id, chapter, verse, text) for book_id, _, chapter, verse, text in iter_verses(corpus)),
        )


def update_langver() -> None:
    path = ROOT / "langver.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    entry = {
        "version": VERSION,
        "name": NAME,
        "nativeName": NATIVE_NAME,
        "languageTag": LANGUAGE_TAG,
        "direction": DIRECTION,
        "files": {
            "csv": f"formats/csv/{VERSION}.csv",
            "json": f"formats/json/{VERSION}.json",
            "yaml": f"formats/yaml/{VERSION}.yaml",
            "sql": f"formats/sql/{VERSION}.sql",
            "md": f"formats/md/{VERSION}.md",
            "txt": f"formats/txt/{VERSION}.txt",
            "sqlite": f"formats/sqlite/{VERSION}.db",
        },
    }
    versions = [item for item in data.get(LANG, []) if item.get("version") != VERSION]
    versions.append(entry)
    data[LANG] = versions
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_audit(audit: dict[str, Any]) -> None:
    json_path = ROOT / "reports" / "arabic_svd_import_audit.json"
    md_path = ROOT / "reports" / "arabic_svd_import_audit.md"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = audit["counts"]
    samples = audit["samples"]
    md = [
        "# Arabic SVD Import Audit",
        "",
        f"- Source: {audit['source']['tree_url']}",
        f"- Source commit: `{audit['source']['commit']}`",
        f"- License: {audit['source']['license']}",
        f"- Metadata: `{LANG}/{VERSION}` (`{LANGUAGE_TAG}`), direction `{DIRECTION}`",
        "",
        "## Coverage",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Source files | {counts['source_files']} |",
        f"| Source records | {counts['source_records']} |",
        f"| Books | {counts['books']} |",
        f"| Chapters | {counts['chapters']} |",
        f"| Verses | {counts['verses']} |",
        f"| Empty verses | {counts['empty_verses']} |",
        "",
        "## Samples",
        "",
        f"- Genesis 1:1: {samples['Genesis 1:1']}",
        f"- John 3:16: {samples['John 3:16']}",
        "",
    ]
    md_path.write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ensure_output_dirs()
    corpus, audit = build_corpus()
    write_json(corpus)
    write_csv(corpus)
    write_yaml(corpus)
    write_markdown(corpus)
    write_text(corpus)
    write_sql(corpus)
    write_sqlite(corpus)
    update_langver()
    write_audit(audit)
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
