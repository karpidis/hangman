import sqlite3 
import json
import os
import sys
import unicodedata import normalize, category

#resolve paths to the database 
# __file__ is hangman_flask/app/game_logic.py
#DB_ROOT is hangman_flask/db/
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_FLASK_DIR = os.path.dirname(_APP_DIR)
BASE_DIR = os.path.dirname(_FLASK_DIR)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if os.path.join(BASE_DIR, "usermanager") not in sys.path:
    sys.path.insert(0, BASE_DIR)

from elocalculator import difr

DB_ROOT = os.path.join(BASE_DIR, "db")
MAIN_DB = os.path.join(DB_ROOT, "Main.db")
USERS_DB = os.path.join(DB_ROOT, "Users.db")

K_FACTOR = 20

# ------ Database connection functions ------

def main_db():
    """Connect to the main database."""
    con = sqlite3.connect(MAIN_DB)
    con.row_factory = sqlite3.Row
    return con


def users_db():
    """Connect to the users database."""
    con = sqlite3.connect(USERS_DB)
    con.row_factory = sqlite3.Row
    return con


#------ Language Dictionary Word List Functions ------

def load_languages() -> list[dict]:
    """Load the list of languages from the main database."""
    con = main_db()
    rows = con.execute(
        "SELECT id, name, code FROM languages ORDER BY name"
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]

def load_dictionaries(language_id: int) -> list[dict]:
    """Load the list of dictionaries for a given language from the main database."""
    con = main_db()
    rows = con.execute(
        "SELECT id, dictionary_name, source "
        "FROM dictionaries WHERE language_id = ? ",
        (language_id,)
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]

