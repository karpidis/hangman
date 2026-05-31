#!/usr/bin/env python3
"""
Clean all JSON dictionary files in place:
  - Decode HTML entities in all text fields
  - Remove duplicate words (keep first occurrence)
  - Remove words with spaces (multi-word phrases)
  - Remove words shorter than 3 characters
Then re-import cleaned files into the SQLite databases.
"""

import json
import os
import html
import sqlite3
import create_databases as db

BASE = os.path.dirname(os.path.abspath(__file__))

# All basic dictionary files to clean
FILES = [
    ('en', 'en/basic.json'),
    ('de', 'de/basic_de.json'),
    ('pt', 'pt/basic_pt.json'),
    ('tr', 'tr/basic_tr.json'),
    ('pl', 'pl/basic_pl.json'),
    ('fr', 'fr/basic-fr.json'),
    ('es', 'es/basic_es.json'),
    ('el', 'el/basic_el.json'),
    ('ru', 'ru/basic.json'),
    ('sw', 'sw/basic_sw.json'),
    ('it', 'it/basic.json'),
]

TEXT_FIELDS = ['word', 'translation', 'definition', 'etymology', 'example']


def clean_entry(entry):
    """Decode HTML entities in all text fields of a word entry."""
    return {k: html.unescape(v) if isinstance(v, str) else v for k, v in entry.items()}


def clean_file(path):
    """Clean a single JSON file and return (original_count, cleaned_count, issues)."""
    with open(path, encoding='utf-8') as f:
        data = json.load(f)

    original = data['words']
    issues = []
    seen = set()
    cleaned = []

    for entry in original:
        entry = clean_entry(entry)
        word = entry.get('word', '').strip()

        if not word:
            issues.append(f'empty word skipped')
            continue
        if len(word) < 3:
            issues.append(f'too short: "{word}"')
            continue
        if ' ' in word:
            issues.append(f'has spaces: "{word}"')
            continue
        if word.lower() in seen:
            issues.append(f'duplicate: "{word}"')
            continue

        seen.add(word.lower())
        entry['word'] = word
        cleaned.append(entry)

    data['words'] = cleaned

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return len(original), len(cleaned), issues


def reimport_language(lang_code, lang_name):
    """Clear and re-import a language's dictionary into the SQLite databases."""
    main_con = sqlite3.connect(db.MAIN_DB)
    main_cur = main_con.cursor()

    # Get language id
    main_cur.execute("SELECT id FROM languages WHERE code = ?", (lang_code,))
    lang_id = main_cur.fetchone()[0]

    # Remove existing dictionary registrations for this language
    main_cur.execute("DELETE FROM dictionaries WHERE language_id = ?", (lang_id,))
    main_con.commit()
    main_con.close()

    # Clear words from the language DB
    lang_db_path = os.path.join(db.DB_ROOT, lang_code, f"{lang_name}.db")
    if os.path.exists(lang_db_path):
        lang_con = sqlite3.connect(lang_db_path)
        lang_con.execute("DELETE FROM words")
        lang_con.commit()
        lang_con.close()

    # Re-import
    db.process_language(lang_name, lang_code)


if __name__ == "__main__":
    print("=== Cleaning JSON files ===\n")

    for lang_code, rel_path in FILES:
        path = os.path.join(BASE, rel_path)
        before, after, issues = clean_file(path)
        removed = before - after
        status = '✅' if removed == 0 else f'fixed {removed} entries'
        print(f"{lang_code} ({rel_path}): {before} -> {after} words  [{status}]")
        for issue in issues:
            print(f"   - {issue}")

    print("\n=== Re-importing to databases ===\n")

    lang_map = {code: name for name, code, _ in db.LANGUAGES}
    for lang_code, _ in FILES:
        lang_name = lang_map[lang_code]
        print(f"{lang_name} ({lang_code})")
        reimport_language(lang_code, lang_name)

    print("\nDone.")
