import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_DB = os.path.join(BASE_DIR, "Main.db")
ENGLISH_DB = os.path.join(BASE_DIR, "English.db")

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
    print(f"Created {MAIN_DB}")


def create_english_db():
    con = sqlite3.connect(ENGLISH_DB)
    cur = con.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS words (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            dictionary_id INTEGER NOT NULL,
            word          TEXT NOT NULL,
            definition    TEXT,
            etymology     TEXT,
            example       TEXT,
            image         TEXT,
            translation   TEXT
        );
    """)

    con.commit()
    con.close()
    print(f"Created {ENGLISH_DB}")


def populate_english_dictionaries():
    main_con = sqlite3.connect(MAIN_DB)
    main_cur = main_con.cursor()

    en_con = sqlite3.connect(ENGLISH_DB)
    en_cur = en_con.cursor()

    main_cur.execute("SELECT id FROM languages WHERE code = 'en'")
    lang_id = main_cur.fetchone()[0]

    en_dir = os.path.join(BASE_DIR, "en")
    for filename in sorted(os.listdir(en_dir)):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(en_dir, filename)
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        dict_name = data.get("dictionary_name", filename)

        main_cur.execute(
            "INSERT INTO dictionaries (language_id, dictionary_name, source) VALUES (?, ?, ?)",
            (lang_id, dict_name, filename)
        )
        dict_id = main_cur.lastrowid

        rows = []
        for entry in data.get("words", []):
            rows.append((
                dict_id,
                entry.get("word", "").strip(),
                entry.get("definition") or None,
                entry.get("etymology") or None,
                entry.get("example") or None,
                entry.get("image") or None,
                entry.get("translation") or None,
            ))

        en_cur.executemany(
            "INSERT INTO words (dictionary_id, word, definition, etymology, example, image, translation) VALUES (?,?,?,?,?,?,?)",
            rows
        )
        print(f"  Loaded '{dict_name}' ({len(rows)} words) → dict_id={dict_id}")

    main_con.commit()
    en_con.commit()
    main_con.close()
    en_con.close()


if __name__ == "__main__":
    create_main_db()
    create_english_db()
    populate_english_dictionaries()
    print("Done.")
