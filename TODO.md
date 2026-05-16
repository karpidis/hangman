# Hangman Project - TODO

## Phase 1 — Fixes ✅ Complete
- [x] `menu()` dynamic with enumerate — scales automatically with language list
- [x] Languages expanded to 11 (English, French, Spanish, German, Italian, Portuguese, Russian, Greek, Swahili, Turkish, Polish)
- [x] Single-character check in `input_letters()`
- [x] Missing comma after Spanish alphabet fixed
- [x] `ß` added to German alphabet
- [x] `word_information()` called always after game ends, not only on win
- [x] `q` and `x` kept in Swahili (used in loanwords)

## Phase 2 — Game Logic
- [x] Track wrong guess count inside `hangman_game()`
- [x] At 6 wrong guesses: Reveals the word
- [x] Always show `word_information()` at the end regardless of choice

## Phase 3 — Architecture Refactor
- [ ] Separate game logic from interface (print/input calls) to prepare for Qt, web and exe
- [ ] Migrate from JSON files to SQLite — one database, all languages, all words
- [ ] Add guard in `__init__.py` for empty language folders (currently loops forever)

## Phase 4 — Content & Language Management
- [ ] Fill in missing definitions, etymologies and examples in all dictionaries
- [ ] Add ability to add new languages (alphabet + word list) without touching code
- [ ] GPT integration for auto-generating missing word data (placeholder already in code)

## Phase 5 — Delivery Targets
- [ ] Terminal exe via PyInstaller (straightforward once SQLite is in place)
- [ ] Qt desktop version
- [ ] Web version (Flask already started in `hangman_flask/`)
