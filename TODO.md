# Hangman Project - TODO

## Phase 1 — Fixes ✅ Complete
- [x] `menu()` dynamic with enumerate — scales automatically with language list
- [x] Languages expanded to 11 (English, French, Spanish, German, Italian, Portuguese, Russian, Greek, Swahili, Turkish, Polish)
- [x] Single-character check in `input_letters()`
- [x] Missing comma after Spanish alphabet fixed
- [x] `ß` added to German alphabet
- [x] `word_information()` called always after game ends, not only on win
- [x] `q` and `x` kept in Swahili (used in loanwords)

## Phase 2 — Game Logic ✅ Complete
- [x] Track wrong guess count inside `hangman_game()`
- [x] At 6 wrong guesses: show all unguessed letters
- [x] At 6 wrong guesses: ask player to reveal word or keep playing with 0 points
- [x] Always show `word_information()` at the end regardless of choice

## Phase 3 — SQLite Migration ✅ Complete
### 3a — Schema Design ✅
- [x] `Main.db` — ships with app (content only):
  - `languages` (id, name, code, alphabet)
  - `dictionaries` (id, language_id, dictionary_name, source) — registry of dictionary files
  - `word_elo` (word, language_id, elo, attempts, reveals) — universal word difficulty
- [x] `users.db` — local, never shipped:
  - `users` (id, username, email, password, date_joined)
  - `user_language_stats` (user_id, language_id, elo, high_score, best_streak)
  - `sessions` (id, user_id, language_id, dictionary_id, played_at, total_score)
  - `word_attempts` (id, session_id, word, wrong_guesses, points_earned, revealed, played_at)
- [x] `db/<lang>/<Language>.db` — one per language, ships with app:
  - `words` (id, word, translation, definition, etymology, example, dictionary_id)

### 3b — ELO System for Words ✅
- [x] Each word starts at ELO 1000 (c2 words pre-seeded at 2000)
- [x] After every attempt: update word ELO using `difr()` — same formula as player ELO
- [x] Word ELO is global (same across all players) — reflects true difficulty over time
- [x] Points multiplier based on word ELO (0.5× at <1000 up to 6.0× at ≥3000)
- [ ] Use ELO to influence word selection (harder words selected less often for beginners)

### 3c — Migration & Import ✅
- [x] `create_databases.py` — creates/updates Main.db and all language .db files from JSON
- [x] `clean_dictionaries.py` — strips HTML entities, duplicates, multi-word phrases, short words
- [x] `translate_dictionary.py` — translates JSON dictionaries via Google Cloud Translation (OAuth2)
- [ ] XLS import feature — users create dictionaries in Excel, app imports into new dictionary.db

### 3d — Code Refactor ✅
- [x] Replaced JSON loading with SQLite queries in `hangman_international_v3.py`
- [x] Replaced `__init__.py` folder logic with dictionary registry lookup from `Main.db`
- [x] Replaced hardcoded alphabet dict with query from `languages` table
- [x] HANGMAN_STAGES displayed during gameplay
- [x] Game ends after 3 losses (MAX_LOSSES)
- [x] Reveal word on loss; show word info (definition, etymology, example) after every round
- [ ] Auto-detect dictionary files in a designated folder and register in `main.db`
- [ ] Add guard for empty or missing dictionary files

## Phase 4 — Architecture Refactor for Multiple Frontends
- [ ] Separate game logic from interface (print/input calls)
- [ ] Core logic shared across terminal, Qt, web and exe
- [ ] Fix `sys._MEIPASS` path handling for PyInstaller compatibility
- [ ] Remove `importlib.import_module` dynamic imports (solved by SQLite migration)

## Phase 5 — Content & Language Management
- [ ] Fill in missing definitions, etymologies and examples in all dictionaries
- [ ] Add ability to add new languages (alphabet + word list) without touching code
- [ ] GPT integration for auto-generating missing word data (placeholder already in code)

## Phase 6 — Delivery Targets
- [ ] Terminal exe via PyInstaller — one per platform (Windows, Mac, Linux)
- [ ] GitHub Actions for automated builds on all three platforms
- [ ] Qt desktop version
- [ ] Web version (Flask already started in `hangman_flask/`)
