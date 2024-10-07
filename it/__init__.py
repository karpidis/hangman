import json
import os

# Function to return a dictionary with human-readable names as keys and filenames as values
def get_human_readable_names():
    json_files = {}

    # Get the directory where this __init__.py is located
    current_dir = os.path.dirname(__file__)

    # Iterate over all .json files in the current folder (where __init__.py is located)
    for json_file in os.listdir(current_dir):
        if json_file.endswith('.json'):
            json_path = os.path.join(current_dir, json_file)
            # Open and read each JSON file
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Extract the human-readable dictionary name
                if 'dictionary_name' in data:
                    # Map the human-readable name to the filename
                    json_files[data['dictionary_name']] = json_path  # Use full path here

    return json_files

# Removed get_json_file_path() as it is no longer needed

def choose_dictionary():
    files_in_module = get_human_readable_names()

    while True:
        print("Choose a dictionary:")
        for idx, (name, filename) in enumerate(files_in_module.items(), 1):
            print(f"{idx}: {name}")

        # Get user input
        epilogi = None
        while epilogi is None:
            try:
                epilogi = int(input("Enter the number of your choice: "))
                if epilogi in range(1, len(files_in_module) + 1):
                    chosen_name = list(files_in_module.keys())[epilogi - 1]
                    chosen_file = files_in_module[chosen_name]
                    print(f"You chose: {chosen_name}, corresponding file: {chosen_file}")
                    return chosen_file  # Return the full path of the selected JSON file
                else:
                    print("Not a valid option. Try again.")
                    epilogi = None
            except ValueError:
                print("Invalid input. Please enter a number.")
