import csv
import json

# Paths for input CSV and output JSON
csv_path = 'sample_dictionary.csv'
json_filename = ""

# Read the CSV file
with open(csv_path, 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    
    # Skip the header
    header = next(csvreader)
    
    # Extract the dictionary name and JSON filename from the second row
    second_row = next(csvreader)
    dictionary_name = second_row[0]
    json_filename = second_row[1]
    
    # Use the header from the 3rd column onwards for dynamic attributes
    attributes = header[2:]  # Dynamically get attributes starting from the 3rd column
    
    # Initialize list to store words
    words_list = []
    
    # Iterate through the rows for the words
    for row in csvreader:
        if row[2].strip():  # Ensure it's not an empty word
            word_entry = {"word": row[2].strip()}  # Always use "word" as the first attribute
            for i, attr in enumerate(attributes, start=2):  # Loop over the dynamic columns
                if len(row) > i and row[i].strip():
                    word_entry[attr] = row[i].strip()
                else:
                    word_entry[attr] = ""  # Fill empty attributes with an empty string
            
            words_list.append(word_entry)

# Create the final dictionary structure
dictionary_data = {
    "dictionary_name": dictionary_name.strip(),
    "words": words_list
}

# Save as JSON
output_json_path = f'{json_filename.strip()}'
with open(output_json_path, 'w') as json_file:
    json.dump(dictionary_data, json_file, indent=4)

print(f"JSON file created: {output_json_path}")
