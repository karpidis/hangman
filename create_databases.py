import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_ROOT   = os.path.join(BASE_DIR, "db")
MAIN_DB   = os.path.join(BASE_DIR, "Main.db")   # root-level central database

# Set to True to only import files with "basic" in the filename
BASIC_ONLY = True

LANGUAGES = [
    ("English",    "en", {'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'}),
    ("French",     "fr", {'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','à','â','æ','ç','é','è','ê','ë','î','ï','ô','œ','ù','û','ü'}),
    ("Spanish",    "es", {'a','b','c','d','e','f','g','h','i','j','k','l','m','n','ñ','o','p','q','r','s','t','u','v','w','x','y','z','á','é','í','ó','ú','ü'}),
    ("German",     "de", {'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','ä','ö','ü','ß'}),
    ("Italian",    "it", {'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','à','è','é','ì','ò','ù'}),
    ("Portuguese", "pt", {'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','á','é','í','ó','ú','â','ê','ô'}),
    ("Russian",    "ru", {'а','б','в','г','д','е','ё','ж','з','и','й','к','л','м','н','о','п','р','с','т','у','ф','х','ц','ч','ш','щ','ъ','ы','ь','э','ю','я'}),
    ("Greek",      "el", {'α','β','γ','δ','ε','ζ','η','θ','ι','κ','λ','μ','ν','ξ','ο','π','ρ','σ','τ','υ','φ','χ','ψ','ω','ά','έ','ή','ί','ό','ύ','ώ','ϊ','ϋ','ς'}),
    ("Swahili",    "sw", {'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'}),
    ("Turkish",    "tr", {'a','b','c','ç','d','e','f','g','ğ','h','ı','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'}),
    ("Polish",     "pl", {'a','ą','b','c','ć','d','e','ę','f','g','h','i','j','k','l','ł','m','n','ń','o','p','q','r','s','ś','t','u','v','w','x','y','z','ź','ż'}),
]


def create_main_db():
    """Create or update Main.db with the full schema."""
    os.makedirs(DB_ROOT, exist_ok=True)

    con = sqlite3.connect(MAIN_DB)
    cur = con.cursor()
    cur.executescript("""
        PRAGMA foreign_keys = ON;

        -- Language registry with alphabet
        CREATE TABLE IF NOT EXISTS languages (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT NOT NULL UNIQUE,
            code     TEXT NOT NULL UNIQUE,
            alphabet TEXT
        );

        -- Dictionary file registry; UNIQUE prevents duplicates on re-runs
        CREATE TABLE IF NOT EXISTS dictionaries (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            language_id     INTEGER NOT NULL,
            dictionary_name TEXT NOT NULL,
            level           TEXT,
            source          TEXT,
            created_by      TEXT,
            FOREIGN KEY (language_id) REFERENCES languages(id),
            UNIQUE (language_id, source)
        );

        -- Universal word difficulty: shared across all dictionaries for the same language
        CREATE TABLE IF NOT EXISTS word_elo (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            word       TEXT NOT NULL,
            language_id INTEGER NOT NULL,
            elo        INTEGER NOT NULL DEFAULT 1000,
            attempts   INTEGER NOT NULL DEFAULT 0,
            reveals    INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (language_id) REFERENCES languages(id),
            UNIQUE (word, language_id)
        );
    """)

    # Populate languages (safe to re-run)
    for name, code, alphabet in LANGUAGES:
        alphabet_json = json.dumps(sorted(alphabet), ensure_ascii=False)
        cur.execute(
            "INSERT OR IGNORE INTO languages (name, code, alphabet) VALUES (?, ?, ?)",
            (name, code, alphabet_json)
        )

    con.commit()
    con.close()
    print(f"Main DB ready: {MAIN_DB}")


def process_language(lang_name, lang_code):
    """Create dictionary.db for a language and register its dictionaries in Main.db."""
    source_dir  = os.path.join(BASE_DIR, lang_code)         # JSON source: en/, fr/, etc.
    dest_db_dir = os.path.join(DB_ROOT, lang_code)          # Output: db/en/, db/fr/, etc.

    os.makedirs(dest_db_dir, exist_ok=True)
    lang_db_path = os.path.join(dest_db_dir, f"{lang_name}.db")

    # Words table in dictionary.db — no ELO here, ELO lives in Main.db/word_elo
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
        );
    """)

    main_con = sqlite3.connect(MAIN_DB)
    main_cur = main_con.cursor()

    main_cur.execute("SELECT id FROM languages WHERE code = ?", (lang_code,))
    lang_id = main_cur.fetchone()[0]

    if not os.path.exists(source_dir):
        print(f"  No source folder for {lang_name}, skipping.")
        lang_con.close()
        main_con.close()
        return

    for filename in sorted(os.listdir(source_dir)):
        if not filename.endswith(".json"):
            continue
        if BASIC_ONLY and "basic" not in filename.lower():
            continue

        filepath = os.path.join(source_dir, filename)
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        dict_name = data.get("dictionary_name", filename)

        # INSERT OR IGNORE prevents duplicates when script is re-run
        main_cur.execute(
            "INSERT OR IGNORE INTO dictionaries (language_id, dictionary_name, source) VALUES (?, ?, ?)",
            (lang_id, dict_name, filename)
        )
        main_cur.execute(
            "SELECT id FROM dictionaries WHERE language_id = ? AND source = ?",
            (lang_id, filename)
        )
        dict_id = main_cur.fetchone()[0]

        # Only insert words if this dictionary has no words yet
        lang_cur.execute("SELECT COUNT(*) FROM words WHERE dictionary_id = ?", (dict_id,))
        if lang_cur.fetchone()[0] > 0:
            print(f"  Skipped (already imported): {filename}")
            continue

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
            for entry in data.get("words", [])
            if entry.get("word", "").strip()
        ]

        lang_cur.executemany(
            "INSERT INTO words (dictionary_id, word, translation, definition, etymology, example, image) VALUES (?,?,?,?,?,?,?)",
            rows
        )
        print(f"  Imported {len(rows)} words: {filename} -> {lang_name}.db")

    main_con.commit()
    lang_con.commit()
    main_con.close()
    lang_con.close()


if __name__ == "__main__":
    create_main_db()
    for name, code, _ in LANGUAGES:
        print(f"\n{name} ({code})")
        process_language(name, code)
    print("\nDone.")
