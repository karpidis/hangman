from flask import Flask, render_template, request, session, jsonify, redirect, url_for
import sqlite3
import json
import os
from random import choice
from unicodedata import normalize, category

app = Flask(__name__)
app.secret_key = "hangman_secret_change_this"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_ROOT  = os.path.join(BASE_DIR, "db")
MAIN_DB  = os.path.join(DB_ROOT, "Main.db")

MAX_LOSSES   = 3
POINTS_START = 70


def main_db():
    con = sqlite3.connect(MAIN_DB)
    con.row_factory = sqlite3.Row
    return con


def remove_accents(text: str, lang_name: str) -> str:
    text = text.lower()
    if lang_name == "Greek":
        normalised = normalize("NFD", text)
        text = "".join(c for c in normalised if category(c) != "Mn")
        text = text.replace("ς", "σ")
    return text


def load_words(lang_code: str, lang_name: str, dictionary_id: int) -> dict:
    db_path = os.path.join(DB_ROOT, lang_code, f"{lang_name}.db")
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT word, translation, definition FROM words WHERE dictionary_id = ?",
        (dictionary_id,)
    ).fetchall()
    con.close()
    return {
        row["word"]: {
            "translation": row["translation"],
            "definition":  row["definition"],
        }
        for row in rows
    }


@app.route("/")
def index():
    con = main_db()
    languages = con.execute("SELECT id, name, code FROM languages ORDER BY name").fetchall()
    con.close()
    return render_template("index.html", languages=languages)


@app.route("/start", methods=["POST"])
def start():
    lang_id   = int(request.form["language_id"])
    lang_name = request.form["lang_name"]
    lang_code = request.form["lang_code"]
    username  = request.form["username"].strip() or "Player"

    con = main_db()
    dict_row = con.execute(
        "SELECT id FROM dictionaries WHERE language_id = ? LIMIT 1", (lang_id,)
    ).fetchone()
    con.close()

    if not dict_row:
        return "No dictionary found", 400

    dict_id = dict_row["id"]
    words   = load_words(lang_code, lang_name, dict_id)
    word    = choice(list(words.keys()))

    session.clear()
    session["lang_id"]       = lang_id
    session["lang_name"]     = lang_name
    session["lang_code"]     = lang_code
    session["dict_id"]       = dict_id
    session["username"]      = username
    session["word"]          = word
    session["points"]        = POINTS_START
    session["wrong_guesses"] = []
    session["revealed"]      = []
    session["losses"]        = 0
    session["streak"]        = 0
    session["total_pts"]     = 0

    return redirect(url_for("game"))


@app.route("/game")
def game():
    if "word" not in session:
        return redirect(url_for("index"))

    word      = session["word"]
    lang_name = session["lang_name"]
    norm_word = remove_accents(word, lang_name)

    auto_revealed = {norm_word[0], norm_word[-1]}
    revealed_set  = set(session.get("revealed", [])) | auto_revealed

    display = []
    for letter in word:
        norm = remove_accents(letter, lang_name)
        display.append(letter if norm in revealed_set else "_")

    wrong      = session.get("wrong_guesses", [])
    losses     = session.get("losses", 0)
    lives_left = MAX_LOSSES - losses

    return render_template("game.html",
        display    = display,
        wrong      = wrong,
        lives_left = lives_left,
        max_losses = MAX_LOSSES,
        streak     = session.get("streak", 0),
        total_pts  = session.get("total_pts", 0),
        points     = session.get("points", POINTS_START),
        username   = session.get("username", "Player"),
        lang_name  = lang_name,
        won        = ("_" not in display),
        game_over  = (losses >= MAX_LOSSES),
    )


@app.route("/guess", methods=["POST"])
def guess():
    if "word" not in session:
        return jsonify({"error": "no game"}), 400

    data        = request.get_json()
    letter      = data.get("letter", "").lower().strip()
    if not letter or len(letter) != 1:
        return jsonify({"error": "invalid"}), 400

    word        = session["word"]
    lang_name   = session["lang_name"]
    norm_word   = remove_accents(word, lang_name)
    norm_letter = remove_accents(letter, lang_name)

    revealed      = set(session.get("revealed", []))
    auto_revealed = {norm_word[0], norm_word[-1]}
    all_revealed  = revealed | auto_revealed
    wrong         = session.get("wrong_guesses", [])
    points        = session.get("points", POINTS_START)

    if norm_letter in all_revealed or norm_letter in wrong:
        return jsonify({"status": "already_guessed"})

    if norm_letter in set(norm_word):
        revealed.add(norm_letter)
        session["revealed"] = list(revealed)
    else:
        wrong.append(norm_letter)
        session["wrong_guesses"] = wrong
        points = max(0, points - 10)
        session["points"] = points

    all_revealed = revealed | auto_revealed
    display = []
    for ch in word:
        norm = remove_accents(ch, lang_name)
        display.append(ch if norm in all_revealed else "_")

    won       = "_" not in display
    losses    = session.get("losses", 0)
    game_over = False

    if won:
        session["streak"]    = session.get("streak", 0) + 1
        session["total_pts"] = session.get("total_pts", 0) + points
    elif points == 0:
        session["losses"] = losses + 1
        game_over = session["losses"] >= MAX_LOSSES

    return jsonify({
        "status":     "ok",
        "display":    display,
        "wrong":      wrong,
        "points":     points,
        "won":        won,
        "game_over":  game_over,
        "lives_left": MAX_LOSSES - session["losses"],
        "streak":     session.get("streak", 0),
        "total_pts":  session.get("total_pts", 0),
    })


@app.route("/next_word", methods=["POST"])
def next_word():
    if "lang_code" not in session:
        return redirect(url_for("index"))

    words = load_words(session["lang_code"], session["lang_name"], session["dict_id"])
    word  = choice(list(words.keys()))

    session["word"]          = word
    session["points"]        = POINTS_START
    session["wrong_guesses"] = []
    session["revealed"]      = []

    return redirect(url_for("game"))


if __name__ == "__main__":
    app.run(debug=True)
