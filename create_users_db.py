import sqlite3
import os

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
USERS_DB  = os.path.join(BASE_DIR, "users.db")


def create_users_db():
    """Create users.db with all user-related tables. Safe to re-run."""
    con = sqlite3.connect(USERS_DB)
    con.executescript("""
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT NOT NULL UNIQUE,
            email       TEXT NOT NULL UNIQUE,
            password    TEXT NOT NULL,
            date_joined TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Per-language stats and ELO for each user
        CREATE TABLE IF NOT EXISTS user_language_stats (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            language_id INTEGER NOT NULL,
            elo         INTEGER NOT NULL DEFAULT 1000,
            plays       INTEGER NOT NULL DEFAULT 0,
            wins        INTEGER NOT NULL DEFAULT 0,
            high_score  INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE (user_id, language_id)
        );

        -- One session = one full game round
        CREATE TABLE IF NOT EXISTS sessions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            language_id   INTEGER NOT NULL,
            dictionary_id INTEGER NOT NULL,
            played_at     TEXT NOT NULL DEFAULT (datetime('now')),
            total_score   INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        -- One row per word played within a session
        CREATE TABLE IF NOT EXISTS word_attempts (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id    INTEGER NOT NULL,
            word          TEXT NOT NULL,
            wrong_guesses INTEGER NOT NULL DEFAULT 0,
            points_earned INTEGER NOT NULL DEFAULT 0,
            revealed      INTEGER NOT NULL DEFAULT 0,
            played_at     TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
    """)
    con.commit()
    con.close()
    print(f"users.db ready: {USERS_DB}")


if __name__ == "__main__":
    create_users_db()
