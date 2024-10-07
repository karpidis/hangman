import json


def main():
    file_name = "../gr/greek.json"
    processed_words = process_word_list(word_list)
    human_readable_name = "Greek Dictionary"
    save_to_json(processed_words, file_name, human_readable_name)


def process_word_list(wordlist):
    """Process the word list and remove one-letter words."""
    words = wordlist.strip().split("\n")
    processed_words = [word for word in words if len(word) > 1]
    return processed_words


def save_to_json(words, filename, human_readable_name):
    # Prepare the dictionary for JSON
    word_data = {
        "dictionary_name": human_readable_name,
        "words": words
    }

    # Save to JSON file
    with open(filename, 'w') as json_file:
        json.dump(word_data, json_file, indent=4)

    print(f"Word list saved to {filename}")


word_list = """


"""

if __name__ == "__main__":
    main()
