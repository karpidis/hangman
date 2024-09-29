from random import choice
from word_dictionaries import greek_words, c2_words

def main():
    play_again = ""
    while play_again != "1":
        hangman_game(c2_words)
        play_again = input("Press enter to play again or 1 and enter to quit\t")
    return print("Thank you for playing")

def hangman_game(words:list):
    unknown_word = choice(words).lower()
    revealed_letters = {unknown_word[0],unknown_word[-1]}
    print(construct_showing_word(unknown_word,revealed_letters))
    remaining_letters = set(unknown_word) - revealed_letters

    while len(remaining_letters) !=0:
        guessed_letter = input_letters("English")

        if guessed_letter in remaining_letters:
            remaining_letters = remaining_letters - {guessed_letter}
            revealed_letters.add(guessed_letter)
            showing_word = construct_showing_word(unknown_word,revealed_letters)
            print(showing_word[0],"\tGuessed letters:", showing_word[1])
        elif guessed_letter in revealed_letters:
            print(f"The letter {guessed_letter} is already revealed")         
        else:
            print(f"The letter {guessed_letter} is not in the word")
    if len(remaining_letters) == 0:
        print(f'Bravo you found the word {unknown_word}')

def construct_showing_word(word: str, revealed: set = None):
    if revealed is None:
        revealed = {(word[0]), (word[-1])}
    display = ""
    for  i, letter in enumerate(word):
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
        "Russian": {'а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л',
                    'м', 'н', 'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш',
                    'щ', 'ъ', 'ы', 'ь', 'э', 'ю', 'я'},
        "Italian": {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
                    'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
                    'u', 'v', 'w', 'x', 'y', 'z', 'à', 'è', 'é', 'ì', 'ò', 'ù'}
    }

    # Get the valid letter set for the given language code
    valid_letters = alphabet_dict[lang]

    while True:
        # Input from the user
        chosen_letter = input("Please guess a letter: ").lower()

        # Check if the letter is in the valid alphabet for the selected language
        if chosen_letter in valid_letters:
            return chosen_letter
        else:
            print(f"You did not choose a valid letter from the {lang} alphabet. Please try again.")



if __name__ == "__main__":
    main()