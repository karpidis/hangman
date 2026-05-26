import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# New central database directory
DB_ROOT = os.path.join(BASE_DIR, "db")
MAIN_DB = os.path.join(DB_ROOT, "Main.db")

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
    # Ensure the db/ directory exists
    os.makedirs(DB_ROOT, exist_ok=True)
    
    con = sqlite3.connect(MAIN_DB)
    cur = con.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS languages (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT NOT NULL UNIQUE,
            code    TEXT NOT NULL UNIQUE,
            alphabet TEXT
        );
        CREATE TABLE IF NOT EXISTS dictionaries (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            language_id     INTEGER NOT NULL,
            dictionary_name TEXT NOT NULL,
            level           TEXT,
            source          TEXT,
            created_by      TEXT,
            FOREIGN KEY (language_id) REFERENCES languages(id)
        );
    """)
    for name, code, alphabet in LANGUAGES:
        alphabet_json = json.dumps(sorted(alphabet), ensure_ascii=False)
        cur.execute(
            "INSERT OR IGNORE INTO languages (name, code, alphabet) VALUES (?, ?, ?)",
            (name, code, alphabet_json)
        )
    con.commit()
    con.close()
    print(f"Main registry: {MAIN_DB}")

def process_language(lang_name, lang_code):
    """Handles directory creation, DB setup, and data import for a language."""
    # Source folder where JSONs are (at script root)
    source_dir = os.path.join(BASE_DIR, lang_code)
    # Destination folder for the DB (inside db/)
    dest_db_dir = os.path.join(DB_ROOT, lang_code)
    
    os.makedirs(dest_db_dir, exist_ok=True)
    lang_db_path = os.path.join(dest_db_dir, f"{lang_name}.db")

    # 1. Initialize the local language DB
    lang_con = sqlite3.connect(lang_db_path)
    lang_cur = lang_con.cursor()
    lang_cur.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            dictionary_id INTEGER NOT NULL,
            word          TEXT NOT NULL,
            definition    TEXT,
            etymology     TEXT,
            example       TEXT,
            image         TEXT,
            translation   TEXT,
            elo           INTEGER DEFAULT 1000
        );
    """)

    # 2. Get Lang ID from Main DB
    main_con = sqlite3.connect(MAIN_DB)
    main_cur = main_con.cursor()
    main_cur.execute("SELECT id FROM languages WHERE code = ?", (lang_code,))
    lang_id = main_cur.fetchone()[0]

    # 3. Look for JSON files in the source directory (root/en, root/fr, etc.)
    if os.path.exists(source_dir):
        for filename in sorted(os.listdir(source_dir)):
            if not filename.endswith(".json"):
                continue
            if BASIC_ONLY and "basic" not in filename:
                continue

            filepath = os.path.join(source_dir, filename)
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

            dict_name = data.get("dictionary_name", filename)
            default_elo = data.get("default_elo", 1000)

            # Register in Main.db
            main_cur.execute(
                "INSERT INTO dictionaries (language_id, dictionary_name, source) VALUES (?, ?, ?)",
                (lang_id, dict_name, filename)
            )
            dict_id = main_cur.lastrowid

            # Insert words into the language DB inside db/
            rows = []
            for entry in data.get("words", []):
                rows.append((
                    dict_id,
                    entry.get("word", "").strip(),
                    entry.get("definition"),
                    entry.get("etymology"),
                    entry.get("example"),
                    entry.get("image"),
                    entry.get("translation"),
                    default_elo,
                ))

            lang_cur.executemany(
                "INSERT INTO words (dictionary_id, word, definition, etymology, example, image, translation, elo) VALUES (?,?,?,?,?,?,?,?)",
                rows
            )
            print(f"  Done: {filename} -> {lang_name}.db")

    main_con.commit()
    lang_con.commit()
    main_con.close()
    lang_con.close()

if __name__ == "__main__":
    create_main_db()
    
    for name, code, _ in LANGUAGES:
        print(f"Checking {name} ({code})...")
        process_language(name, code)
    
    print("\nProcessing complete.")