import sqlite3
import json
import os
from random import choice

from usermanager import login_or_register, update_stats
from usermanager.usermanager import get_or_create_language_stats
from elocalculator import difr

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
MAIN_DB   = os.path.join(BASE_DIR, "Main.db")   # ships with app — content only
USERS_DB  = os.path.join(BASE_DIR, "users.db")  # local — created on first run
DB_ROOT   = os.path.join(BASE_DIR, "db")

K_FACTOR = 20

HANGMAN_STAGES = [
    "  -----\n  |   |\n  |\n  |\n  |\n  |\n__|__",
    "  -----\n  |   |\n  |   O\n  |\n  |\n  |\n__|__",
    "  -----\n  |   |\n  |   O\n  |   |\n  |\n  |\n__|__",
    "  -----\n  |   |\n  |   O\n  |   |\n  |   |\n  |\n__|__",
    "  -----\n  |   |\n  |   O\n  |   |\n  |  /|\n  |\n__|__",
    "  -----\n  |   |\n  |   O\n  |   |\n  |  /|\\\n  |\n__|__",
    "  -----\n  |   |\n  |   O\n  |   |\n  |  /|\\\n  |  /\n__|__",
    "  -----\n  |   |\n  |   O\n  |   |\n  |  /|\\\n  |  / \\\n__|__",
]


# ── Database helpers ──────────────────────────────────────────────────────────

def main_db():
    con = sqlite3.connect(MAIN_DB)
    con.row_factory = sqlite3.Row
    return con


def load_languages():
    """Return all languages from Main.db ordered by name."""
    con = main_db()
    rows = con.execute("SELECT id, name, code FROM languages ORDER BY name").fetchall()
    con.close()
    return rows


def choose_dictionary(language_id: int):
    """Return chosen dictionary row from Main.db. Auto-selects if only one exists."""
    con = main_db()
    dicts = con.execute(
        "SELECT id, dictionary_name, source FROM dictionaries WHERE language_id = ?",
        (language_id,)
    ).fetchall()
    con.close()

    if not dicts:
        print("No dictionaries found for this language.")
        return None

    if len(dicts) == 1:
        return dicts[0]

    options = {str(i): d for i, d in enumerate(dicts, 1)}
    while True:
        print("\nChoose a dictionary:")
        for num, d in options.items():
            print(f"  {num}. {d['dictionary_name']}")
        pick = input("Your choice: ").strip()
        if pick in options:
            return options[pick]
        print(f"Choose a number between 1-{len(options)}")


def load_words(lang_code: str, lang_name: str, dictionary_id: int) -> dict:
    """Load words from the language's dictionary.db into a {word: info} dict."""
    db_path = os.path.join(DB_ROOT, lang_code, f"{lang_name}.db")
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT word, translation, definition, etymology, example FROM words WHERE dictionary_id = ?",
        (dictionary_id,)
    ).fetchall()
    con.close()

    return {
        row["word"]: {
            "translation": row["translation"],
            "definition":  row["definition"],
            "etymology":   row["etymology"],
            "example":     row["example"],
        }
        for row in rows
    }


def get_alphabet(language_id: int) -> set:
    """Load valid alphabet letters for a language from Main.db."""
    con = main_db()
    row = con.execute("SELECT alphabet FROM languages WHERE id = ?", (language_id,)).fetchone()
    con.close()
    return set(json.loads(row["alphabet"]))


def get_word_elo(language_id: int, word: str) -> int:
    """Return word ELO from Main.db, defaulting to 1000 if not seen before."""
    con = main_db()
    row = con.execute(
        "SELECT elo FROM word_elo WHERE language_id = ? AND word = ?",
        (language_id, word)
    ).fetchone()
    con.close()
    return row["elo"] if row else 1000


def users_db():
    con = sqlite3.connect(USERS_DB)
    con.row_factory = sqlite3.Row
    return con


def record_game(user_id: int, language_id: int, dictionary_id: int,
                word: str, wrong_guesses: int, points: int, revealed: bool,
                user_elo: int = 1000, current_word_elo: int = 1000):
    """Write session + word_attempt to users.db; update word ELO in Main.db."""

    # sessions and word_attempts are personal data → users.db
    ucon = users_db()
    ucon.execute(
        "INSERT INTO sessions (user_id, language_id, dictionary_id, total_score) VALUES (?,?,?,?)",
        (user_id, language_id, dictionary_id, points)
    )
    session_id = ucon.execute("SELECT last_insert_rowid()").fetchone()[0]
    ucon.execute(
        "INSERT INTO word_attempts (session_id, word, wrong_guesses, points_earned, revealed) VALUES (?,?,?,?,?)",
        (session_id, word, wrong_guesses, points, int(revealed))
    )
    ucon.commit()
    ucon.close()

    # Word ELO is fully symmetric with player ELO — same difr, binary result.
    # Player won = word lost (0.0), player lost = word won (1.0)
    word_result = 0.0 if not revealed else 1.0
    elo_change  = round(difr(current_word_elo, user_elo, word_result, K_FACTOR))

    mcon = main_db()
    mcon.execute(
        "INSERT OR IGNORE INTO word_elo (word, language_id, elo, attempts, reveals) VALUES (?,?,1000,0,0)",
        (word, language_id)
    )
    mcon.execute("""
        UPDATE word_elo SET
            attempts = attempts + 1,
            reveals  = reveals + ?,
            elo      = MAX(0, elo + ?)
        WHERE word = ? AND language_id = ?
    """, (int(revealed), elo_change, word, language_id))
    mcon.commit()
    mcon.close()


# ── Game UI ───────────────────────────────────────────────────────────────────

def menu(languages) -> dict:
    options = {str(i): lang for i, lang in enumerate(languages, 1)}
    while True:
        print("\nChoose a language:")
        for num, lang in options.items():
            print(f"  {num}. {lang['name']}")
        pick = input("Your choice: ").strip()
        if pick in options:
            return options[pick]
        print(f"Choose a number between 1-{len(options)}")


def hangman_game(words: dict, lang_name: str, alphabet: set) -> tuple[int, bool, str, int]:
    """Returns (points, won, word, wrong_guesses)."""
    points        = 70
    wrong_guesses = 0
    word          = choice(list(words.keys()))
    revealed      = {word[0], word[-1]}
    remaining     = set(word) - revealed

    print(HANGMAN_STAGES[wrong_guesses])
    print(construct_showing_word(word, revealed), "\tGuessed:", sorted(revealed))

    while points > 0 and remaining:
        letter = input_letter(lang_name, alphabet)

        if letter in remaining:
            remaining.discard(letter)
            revealed.add(letter)
            print(HANGMAN_STAGES[wrong_guesses])
            print(construct_showing_word(word, revealed), "\tGuessed:", sorted(revealed))
        elif letter in revealed:
            print(f"'{letter}' is already revealed.")
            print(HANGMAN_STAGES[wrong_guesses])
            print(construct_showing_word(word, revealed), "\tGuessed:", sorted(revealed))
        else:
            wrong_guesses += 1
            points -= 10
            print(f"'{letter}' is not in the word.")
            print(HANGMAN_STAGES[wrong_guesses])
            print(construct_showing_word(word, revealed), "\tGuessed:", sorted(revealed))

    won = not remaining
    if won:
        msg = f"Correct! '{word}' — {points} points" if points > 0 else f"Correct! '{word}' — 0 points"
        print(msg)
    else:
        print(f"\nThe word was: '{word}'")

    word_information(word, words)
    return points, won, word, wrong_guesses


def construct_showing_word(word: str, revealed: set) -> str:
    return " ".join(letter if letter in revealed else "_" for letter in word)


def word_information(word: str, glossary: dict):
    info = glossary.get(word, {})
    fields = [
        ("Translation", info.get("translation")),
        ("Definition",  info.get("definition")),
        ("Etymology",   info.get("etymology")),
        ("Example",     info.get("example")),
    ]
    available = [(label, value) for label, value in fields if value]
    if available:
        print()
        for label, value in available:
            print(f"  {label:12}: {value}")


def input_letter(lang_name: str, alphabet: set) -> str:
    while True:
        letter = input("Guess a letter: ").lower()
        if len(letter) != 1:
            print("Enter one letter only.")
            continue
        if letter in alphabet:
            return letter
        print(f"'{letter}' is not a valid letter in the {lang_name} alphabet.")


# ── Main ──────────────────────────────────────────────────────────────────────

def show_stats(user, db_session, lang_id, lang_name, total_points, session_streak):
    """Print current language stats."""
    stats = get_or_create_language_stats(user, db_session, lang_id)
    print(f"\n{'─' * 40}")
    print(f"  Player      : {user.username}")
    print(f"  Language    : {lang_name}")
    print(f"  {'─' * 36}")
    print(f"  ELO         : {stats.elo}")
    print(f"  High Score  : {stats.high_score}")
    print(f"  Best Streak : {stats.best_streak} words")
    print(f"  Session     : {total_points} pts  |  streak {session_streak}")
    print(f"{'─' * 40}\n")
    return stats


def main():
    languages = load_languages()
    user, db_session = login_or_register()

    language   = menu(languages)
    lang_id    = language["id"]
    lang_name  = language["name"]
    lang_code  = language["code"]

    dictionary = choose_dictionary(lang_id)
    if not dictionary:
        return

    words    = load_words(lang_code, lang_name, dictionary["id"])
    alphabet = get_alphabet(lang_id)

    total_points    = 0
    losses          = 0
    session_streak  = 0
    MAX_LOSSES      = 3
    stats = show_stats(user, db_session, lang_id, lang_name, total_points, session_streak)

    while True:
        points, won, word, wrong_guesses = hangman_game(words, lang_name, alphabet)
        total_points += points

        if won:
            session_streak += 1
        else:
            losses += 1

        word_elo  = get_word_elo(lang_id, word)
        elo_delta = difr(stats.elo, word_elo, 1.0 if won else 0.0, K_FACTOR)

        update_stats(user, db_session, lang_id, score=total_points, streak=session_streak, elo_delta=elo_delta)
        record_game(user.id, lang_id, dictionary["id"], word, wrong_guesses, points,
                    revealed=not won, user_elo=stats.elo, current_word_elo=word_elo)

        stats = get_or_create_language_stats(user, db_session, lang_id)
        print(f"\nTotal points: {total_points}  |  ELO: {stats.elo} ({'+' if elo_delta >= 0 else ''}{round(elo_delta)})")

        if losses >= MAX_LOSSES:
            print(f"\nGame over — {MAX_LOSSES} words not guessed. Final score: {total_points}  |  Streak: {session_streak}")
            break

        while True:
            choice = input("\nEnter to play again  |  s = stats  |  1 = quit: ").strip().lower()
            if choice == "":
                break
            elif choice == "s":
                show_stats(user, db_session, lang_id, lang_name, total_points, session_streak)
            elif choice == "1":
                db_session.close()
                print(f"Thanks for playing, {user.username}!")
                return

    db_session.close()
    print(f"Thanks for playing, {user.username}!")


if __name__ == "__main__":
    main()
