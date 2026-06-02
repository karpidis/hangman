"""
Import a JSON dictionary file into the existing databases.

Usage:
    python import_dictionary.py <path/to/file.json> <language_code>

Example:
    python import_dictionary.py my_words.json en
    python import_dictionary.py /tmp/french_slang.json fr

JSON format expected:
    {
        "dictionary_name": "My Dictionary",   <- optional, defaults to filename
        "words": [
            {
                "word": "abandon",
                "translation": "...",          <- all fields optional
                "definition": "...",
                "etymology": "...",
                "example": "...",
                "image": "..."
            },
            ...
        ]
    }
"""

import sqlite3
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_DB  = os.path.join(BASE_DIR, "Main.db")
DB_ROOT  = os.path.join(BASE_DIR, "db")

DEFAULT_WORD_ELO = 1000


def import_json(json_path: str, lang_code: str):
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        sys.exit(1)

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    filename    = os.path.basename(json_path)
    dict_name   = data.get("dictionary_name") or os.path.splitext(filename)[0]
    words_data  = data.get("words", [])

    if not words_data:
        print("No words found in JSON.")
        sys.exit(1)

    # Look up language in Main.db
    main_con = sqlite3.connect(MAIN_DB)
    main_con.row_factory = sqlite3.Row
    main_cur = main_con.cursor()

    row = main_cur.execute("SELECT id, name FROM languages WHERE code = ?", (lang_code,)).fetchone()
    if not row:
        print(f"Language code '{lang_code}' not found in Main.db.")
        print("Available codes:")
        for r in main_cur.execute("SELECT code, name FROM languages ORDER BY name"):
            print(f"  {r['code']}  {r['name']}")
        main_con.close()
        sys.exit(1)

    lang_id   = row["id"]
    lang_name = row["name"]

    # Register the dictionary (unique by language + source filename)
    main_cur.execute(
        "INSERT OR IGNORE INTO dictionaries (language_id, dictionary_name, source) VALUES (?, ?, ?)",
        (lang_id, dict_name, filename)
    )
    # If it already existed, update the name in case it changed
    main_cur.execute(
        "UPDATE dictionaries SET dictionary_name = ? WHERE language_id = ? AND source = ?",
        (dict_name, lang_id, filename)
    )
    dict_id = main_cur.execute(
        "SELECT id FROM dictionaries WHERE language_id = ? AND source = ?",
        (lang_id, filename)
    ).fetchone()["id"]

    main_con.commit()

    # Open the language word DB
    lang_db_dir  = os.path.join(DB_ROOT, lang_code)
    lang_db_path = os.path.join(lang_db_dir, f"{lang_name}.db")

    os.makedirs(lang_db_dir, exist_ok=True)
    lang_con = sqlite3.connect(lang_db_path)
    lang_cur = lang_con.cursor()

    lang_cur.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            dictionary_id INTEGER NOT NULL,
            word          TEXT NOT NULL,
            translation   TEXT,
            definition    TEXT,
            etymology     TEXT,
            example       TEXT,
            image         TEXT
        )
    """)

    # Count existing words for this dictionary
    existing = lang_cur.execute(
        "SELECT COUNT(*) FROM words WHERE dictionary_id = ?", (dict_id,)
    ).fetchone()[0]

    rows = [
        (
            dict_id,
            entry.get("word", "").strip(),
            entry.get("translation"),
            entry.get("definition"),
            entry.get("etymology"),
            entry.get("example"),
            entry.get("image"),
        )
        for entry in words_data
        if entry.get("word", "").strip()
    ]

    if existing > 0:
        print(f"Dictionary '{dict_name}' already has {existing} words.")
        answer = input("Re-import and overwrite? [y/N] ").strip().lower()
        if answer != "y":
            print("Cancelled.")
            lang_con.close()
            main_con.close()
            return
        lang_cur.execute("DELETE FROM words WHERE dictionary_id = ?", (dict_id,))

    lang_cur.executemany(
        "INSERT INTO words (dictionary_id, word, translation, definition, etymology, example, image) VALUES (?,?,?,?,?,?,?)",
        rows
    )
    lang_con.commit()

    # Seed word_elo for new words (INSERT OR IGNORE preserves existing ELO)
    elo_rows = [(w[1], lang_id) for w in rows]
    main_cur.executemany(
        "INSERT OR IGNORE INTO word_elo (word, language_id, elo, attempts, reveals) VALUES (?, ?, ?, 0, 0)",
        [(word, lid, DEFAULT_WORD_ELO) for word, lid in elo_rows]
    )
    main_con.commit()

    lang_con.close()
    main_con.close()

    print(f"\nImported {len(rows)} words into '{lang_name}.db'")
    print(f"  Dictionary : {dict_name}  (id={dict_id})")
    print(f"  Language   : {lang_name} ({lang_code})")
    print(f"  Source     : {filename}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python import_dictionary.py <path/to/file.json> <language_code>")
        print("Example: python import_dictionary.py my_words.json en")
        sys.exit(1)

    import_json(sys.argv[1], sys.argv[2])
