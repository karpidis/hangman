from random import choice
import json
import importlib

from usermanager import login_or_register, update_stats
from elocalculator import difr

WORD_ELO = 1000
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

languages = {
    "English": "en",
    "French": "fr",
    "Spanish": "es",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Russian": "ru",
    "Greek": "el",
    "Swahili": "sw",
    "Turkish": "tr",
    "Polish": "pl"
}


def main():
    user, session = login_or_register()

    total_points = 0
    language = menu()
    ln = languages[language]
    lexiko_module = importlib.import_module(f"{ln}.__init__")
    json_file_path = lexiko_module.choose_dictionary()
    lexiko = read_json_create_dictionary(json_file_path)
    lexiko_words = set(lexiko.keys())

    play_again = ""
    while play_again != "1":
        score, won = hangman_game(lexiko_words, language, lexiko)
        total_points += score
        elo_delta = difr(user.elo, WORD_ELO, 1.0 if won else 0.0, K_FACTOR)
        update_stats(user, session, won=won, score=total_points, elo_delta=elo_delta)
        print("Your total points are:\t", total_points)
        print(f"ELO: {user.elo} ({'+' if elo_delta >= 0 else ''}{round(elo_delta)})")
        play_again = input("Press Enter to play again or 1 and Enter to quit\t")

    username = user.username
    session.close()
    print("Thank you for playing,", username)


def menu():
    language_options = {str(i): lang for i, lang in enumerate(languages, 1)}
    while True:
        language_choice = input(f"Choose the language you want to play {language_options}:\t")
        if language_choice in language_options:
            return language_options[language_choice]
        print(f"Choose a number between 1-{len(language_options)} and press Enter")


def read_json_create_dictionary(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    word_dict = {}
    for entry in data['words']:
        word = entry['word'].strip()
        if len(word) < 3 or " " in word:
            continue
        word_dict[word] = {key: value for key, value in entry.items() if key != 'word'}
    return word_dict


def hangman_game(words: set, lang, glossary) -> tuple[int, bool]:
    """Returns (points_earned, won)."""
    points = 70
    wrong_guesses = 0
    unknown_word = choice(list(words))
    revealed_letters = {unknown_word[0], unknown_word[-1]}
    showing_word = construct_showing_word(unknown_word, revealed_letters)
    print(HANGMAN_STAGES[wrong_guesses])
    print(showing_word[0], "\tGuessed letters:", showing_word[1])
    remaining_letters = set(unknown_word) - revealed_letters

    while points != 0 and len(remaining_letters) != 0:
        guessed_letter = input_letters(lang)

        if guessed_letter in remaining_letters:
            remaining_letters.remove(guessed_letter)
            revealed_letters.add(guessed_letter)
            showing_word = construct_showing_word(unknown_word, revealed_letters)
            print(HANGMAN_STAGES[wrong_guesses])
            print(showing_word[0], "\tGuessed letters:", showing_word[1])
        elif guessed_letter in revealed_letters:
            print(f"The letter {guessed_letter} is already revealed")
            print(HANGMAN_STAGES[wrong_guesses])
            print(showing_word[0], "\tGuessed letters:", showing_word[1])
        else:
            wrong_guesses += 1
            points -= 10
            print(f"The letter {guessed_letter} is not in the word")
            print(HANGMAN_STAGES[wrong_guesses])
            print(showing_word[0], "\tGuessed letters:", showing_word[1])

    won = len(remaining_letters) == 0
    if won:
        if points > 0:
            print(f"Bravo! You found '{unknown_word}' and earned {points} points")
        else:
            print(f"Bravo! You found '{unknown_word}' but with 0 points")
    else:
        points = 0
        print(f"Sorry, the word was '{unknown_word}'")

    word_information(unknown_word, glossary)
    return points, won


def word_information(word: str, glossary: dict):
    info = glossary[word]
    if info.get('translation'):
        print(f"Translation: {info['translation']}")
    if info.get('definition'):
        print(f"Definition: {info['definition']}")
    if info.get('etymology'):
        print(f"Etymology: {info['etymology']}")
    if info.get('example'):
        print(f"Example: {info['example']}")


def construct_showing_word(word: str, revealed: set = None):
    if revealed is None:
        revealed = {word[0], word[-1]}
    display = " ".join(letter if letter in revealed else "_" for letter in word)
    return display, revealed


def input_letters(lang):
    alphabet_dict = {
        "English": set('abcdefghijklmnopqrstuvwxyz'),
        "Greek": {'α','β','γ','δ','ε','ζ','η','θ','ι','κ','λ','μ','ν','ξ','ο','π','ρ','σ','τ','υ','φ','χ','ψ','ω','ά','έ','ή','ί','ό','ύ','ώ','ϊ','ϋ','ς'},
        "German": set('abcdefghijklmnopqrstuvwxyz') | {'ä','ö','ü','ß'},
        "Portuguese": set('abcdefghijklmnopqrstuvwxyz') | {'á','é','í','ó','ú','â','ê','ô'},
        "Russian": {'а','б','в','г','д','е','ё','ж','з','и','й','к','л','м','н','о','п','р','с','т','у','ф','х','ц','ч','ш','щ','ъ','ы','ь','э','ю','я'},
        "Italian": set('abcdefghijklmnopqrstuvwxyz') | {'à','è','é','ì','ò','ù'},
        "Spanish": set('abcdefghijklmnopqrstuvwxyz') | {'ñ','á','é','í','ó','ú','ü'},
        "Swahili": set('abcdefghijklmnopqrstuvwxyz'),
        "Turkish": set('abcdefghijklmnopqrstuvwxyz') | {'ç','ğ','ı','ö','ş','ü'},
        "Polish": set('abcdefghijklmnopqrstuvwxyz') | {'ą','ć','ę','ł','ń','ó','ś','ź','ż'},
        "French": set('abcdefghijklmnopqrstuvwxyz') | {'à','â','æ','ç','é','è','ê','ë','î','ï','ô','œ','ù','û','ü'},
    }
    valid_letters = alphabet_dict[lang]
    while True:
        chosen_letter = input("Please guess a letter: ").lower()
        if len(chosen_letter) != 1:
            print("Please enter only one letter.")
            continue
        if chosen_letter in valid_letters:
            return chosen_letter
        print(f"'{chosen_letter}' is not a valid letter in the {lang} alphabet. Please try again.")


if __name__ == "__main__":
    main()
