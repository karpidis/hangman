from random import choice
import json
import importlib

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
    total_points = 0
    language = menu()
    ln = languages[language]
    lexiko_module = importlib.import_module(f"{ln}.__init__")

    # Call the function from __init__.py to get the JSON file path
    json_file_path = lexiko_module.choose_dictionary()

    lexiko = read_json_create_dictionary(json_file_path)

    lexiko_words = set(lexiko.keys())
    play_again = ""
    while play_again != "1":
        total_points = hangman_game(lexiko_words, language, total_points, lexiko)
        print("Your total_points are :\t", total_points)
        play_again = input("Press enter to play again or 1 and enter to quit\t")
    return print("Thank you for playing")


def menu():
    language_options = {str(i): lang for i, lang in enumerate(languages, 1)}
    while True:
        language_choice = input(f"choose the language you want to play {language_options}:\t")
        if language_choice in language_options:
            return language_options[language_choice]
        else:
            print(f"Choose a number between 1-{len(language_options)} and press Enter")


def read_json_create_dictionary(json_file):
    # Open the JSON file
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Create a dictionary where each word is a key, and its associated information is the value
    word_dict = {}
    for entry in data['words']:
        word = entry['word']  # 'word' will always be present
        # Create a dictionary for the remaining keys dynamically
        word_dict[word] = {key: value for key, value in entry.items() if key != 'word'}

    return word_dict




def hangman_game(words: set, lang, score, glossary):
    points = 70
    words = list(words)
    unknown_word = choice(words)
    revealed_letters = {unknown_word[0], unknown_word[-1]}
    showing_word = construct_showing_word(unknown_word, revealed_letters)
    print(showing_word[0], "\tRevealed letters:", showing_word[1])
    remaining_letters = set(unknown_word) - revealed_letters

    while points != 0 and len(remaining_letters) != 0:
        guessed_letter = input_letters(lang)

        if guessed_letter in remaining_letters:
            remaining_letters = remaining_letters - {guessed_letter}
            revealed_letters.add(guessed_letter)
            showing_word = construct_showing_word(unknown_word, revealed_letters)
            print(showing_word[0], "\tGuessed letters:", showing_word[1])
        elif guessed_letter in revealed_letters:
            print(f"The letter {guessed_letter} is already revealed")
            print(showing_word[0], "\tGuessed letters:", showing_word[1])
        else:
            print(f"The letter {guessed_letter} is not in the word")
            print(showing_word[0], "\tGuessed letters:", showing_word[1])
            points -= 10
    if len(remaining_letters) == 0:
        if points > 0:
            print(f'Bravo you found the word {unknown_word} and you earned {points} points')
            score += points
        else:
            print(f'Bravo you found the word {unknown_word} but with 0 points')
    else:
        print(f'Sorry you didn\'t guess the word, it was {unknown_word}')
    word_information(unknown_word,glossary)
    return score

def word_information(word:str, glossary: dict):
    word_info = glossary[word]
    if 'translation' in word_info and word_info["translation"]:
        print(f"Translation: {word_info['translation']}")
    if 'definition' in word_info and word_info['definition']: #first check is if key existed, and the second if != None
        print(f"Definition: {word_info['definition']}")
    if 'etymology' in word_info and word_info['etymology']: #first check is if key existed, and the second if != None
        print(f"Etymology: {word_info['etymology']}")
    if 'example' in word_info and word_info['example']:
        print(f"Example: {word_info['example']}")
    else:
        #here I will use GPT in later version
        #chatgpt_assistant.generate_missing_data(word, "English")
        return None


def construct_showing_word(word: str, revealed: set = None):
    if revealed is None:
        revealed = {(word[0]), (word[-1])}
    display = ""
    for i, letter in enumerate(word):
        if letter in revealed:
            display += letter
            display += " "
        else:
            display += "_ "
    return display, revealed


def input_letters(lang):
    # Define the sets of valid letters for each language using ISO language codes
    alphabet_dict = {
        "English": {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
                    'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
                    'u', 'v', 'w', 'x', 'y', 'z'},
        "Greek": {'α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ', 'ν',
                  'ξ', 'ο', 'π', 'ρ', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω', 'ά', 'έ',
                  'ή', 'ί', 'ό', 'ύ', 'ώ', 'ϊ', 'ϋ', 'ς'},
        "German": {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
                   'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
                   'u', 'v', 'w', 'x', 'y', 'z', 'ä', 'ö', 'ü', 'ß'},
        "Portuguese": {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
                       'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
                       'u', 'v', 'w', 'x', 'y', 'z', 'á', 'é', 'í', 'ó',
                       'ú', 'â', 'ê', 'ô'},
        "Russian": {'а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л',
                    'м', 'н', 'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш',
                    'щ', 'ъ', 'ы', 'ь', 'э', 'ю', 'я'},
        "Italian": {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
                    'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
                    'u', 'v', 'w', 'x', 'y', 'z', 'à', 'è', 'é', 'ì', 'ò', 'ù'},
        "Spanish": {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                    'n', 'ñ', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y',
                    'z', 'á', 'é', 'í', 'ó', 'ú', 'ü'},

        "Swahili": {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                    'n', 'o', 'p', 'r', 's', 't', 'u', 'v', 'w', 'y','z', 'q', 'x'},
        "Turkish": {'a', 'b', 'c', 'ç', 'd', 'e', 'f', 'g', 'ğ', 'h', 'ı', 'i',
                    'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
                    'v', 'w', 'x', 'y', 'z'},
        "Polish": {'a', 'ą', 'b', 'c', 'ć', 'd', 'e', 'ę', 'f', 'g', 'h', 'i',
                   'j', 'k', 'l', 'ł', 'm', 'n', 'ń', 'o', 'p', 'q', 'r', 's',
                   'ś', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'ź', 'ż'},
        "French": {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
                   'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x',
                   'y', 'z', 'à', 'â', 'æ', 'ç', 'é', 'è', 'ê', 'ë', 'î',
                   'ï', 'ô', 'œ', 'ù', 'û', 'ü'},
        }

    valid_letters = alphabet_dict[lang]

    while True:
        chosen_letter = input("Please guess a letter: ").lower()
        while len(chosen_letter) != 1:
            print("Please enter only one letter.")
            chosen_letter = input("Please guess a letter: ").lower()
        if chosen_letter in valid_letters:
            return chosen_letter
        else:
            print(f"You did not choose a valid letter from the {lang} alphabet. Please try again.")


if __name__ == "__main__":
    main()
