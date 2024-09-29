import json
import os


# Function to return a dictionary with human-readable names as keys and filenames as values
def get_human_readable_names():
    json_files = {}

    # Iterate over all .json files in the current folder
    for json_file in os.listdir():
        if json_file.endswith('.json'):
            # Open and read each JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Extract the human-readable dictionary name
                if 'dictionary_name' in data:
                    # Map the human-readable name to the filename
                    json_files[data['dictionary_name']] = json_file

    return json_files
