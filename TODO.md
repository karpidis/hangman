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

## Phase 3 — SQLite Migration
### 3a — Schema Design
- [ ] `main.db` — central database:
  - `languages` (id, name, code, alphabet)
  - `dictionaries` (id, language_id, dictionary_name, level, source, created_by) — registry of known dictionary files
  - `users` (id, username, created_at)
  - `sessions` (id, user_id, language_id, dictionary_id, played_at, total_score)
  - `word_attempts` (id, session_id, word_id, wrong_guesses, points_earned, revealed, played_at)
- [ ] `dictionary.db` — one file per dictionary:
  - `words` (id, word, translation, definition, etymology, example, difficulty, elo_rating)

### 3b — ELO System for Words
- [ ] Each word starts at ELO 1000
- [ ] After every attempt: update word ELO based on wrong guesses and whether word was revealed
- [ ] Word ELO is global (same across all players) — reflects true difficulty over time
- [ ] Use ELO to influence word selection (harder words selected less often for beginners)

### 3c — Migration & Import
- [ ] One-time script to read all existing JSON files and import into SQLite dictionary files
- [ ] XLS import feature — users create dictionaries in Excel, app imports into new dictionary.db

### 3d — Code Refactor
- [ ] Replace `read_json_create_dictionary()` with SQLite query
- [ ] Replace `__init__.py` folder logic with dictionary registry lookup from `main.db`
- [ ] Replace hardcoded `alphabet_dict` in `input_letters()` with query from `languages` table
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
