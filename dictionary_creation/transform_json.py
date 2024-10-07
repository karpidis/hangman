import json

# Load the original JSON
with open("greek.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# Create placeholders for definition, etymology, example, and image for each word
updated_words = []
for word in data['words']:
    updated_word = {
        "word": word,
        "definition": "",
        "etymology": "",
        "example": "",
        "image": "",
        "level": ""
    }
    updated_words.append(updated_word)

# Update the original data structure
output_data = {
    "dictionary_name": data['dictionary_name'],
    "words": updated_words
}

# Save the updated JSON file with placeholders
with open("greek.json", "w") as file:
    json.dump(output_data, file, indent=4)

print("JSON file created with placeholders for each word.")
