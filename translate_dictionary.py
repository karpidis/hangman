#!/usr/bin/env python3
"""
Translate a hangman word dictionary JSON to another language using Google Cloud Translation.
Usage: python3 translate_dictionary.py <input_json> <language_code>
Example: python3 translate_dictionary.py en/basic.json de

Requires GOOGLE_APPLICATION_CREDENTIALS set to the OAuth client secret JSON path,
either as an environment variable or in a .env file next to this script.
"""

import json
import sys
import os
import pickle
from google.cloud import translate_v2 as translate
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Permission scope needed to call the Cloud Translation API
SCOPES = ["https://www.googleapis.com/auth/cloud-translation"]

# All supported languages: ISO 639-1 code -> human-readable name
LANGUAGE_NAMES = {
    "en": "English",
    "de": "German",
    "pt": "Portuguese",
    "tr": "Turkish",
    "pl": "Polish",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "ru": "Russian",
    "el": "Greek",
    "sw": "Swahili",
}

# Google Cloud Translation v2 accepts up to 128 strings per request
BATCH_SIZE = 128


def load_credentials(script_dir):
    """Load OAuth credentials from token.pickle cache, refreshing or re-authorizing as needed."""
    token_path = os.path.join(script_dir, "token.pickle")
    credentials = None

    # Reuse saved token from a previous run to avoid opening the browser every time
    if os.path.exists(token_path):
        with open(token_path, "rb") as f:
            credentials = pickle.load(f)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            # Token expired but we have a refresh token — silently get a new one
            credentials.refresh(Request())
        else:
            # No valid token at all: read the client secret path from env or .env file
            client_secret_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if not client_secret_path:
                env_path = os.path.join(script_dir, ".env")
                if os.path.exists(env_path):
                    with open(env_path) as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("GOOGLE_APPLICATION_CREDENTIALS="):
                                client_secret_path = line.split("=", 1)[1].strip()
                                break
            if not client_secret_path or not os.path.exists(client_secret_path):
                print("Error: GOOGLE_APPLICATION_CREDENTIALS not set or file not found.")
                sys.exit(1)
            # Opens a browser window for one-time Google login
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            credentials = flow.run_local_server(port=0)

        # Save token so the next run skips the browser step
        with open(token_path, "wb") as f:
            pickle.dump(credentials, f)

    return credentials


def translate_list(client, items, src_lang, target_lang, label):
    """Translate a list of strings in batches, printing progress as we go."""
    translated = []
    total = len(items)
    for i in range(0, total, BATCH_SIZE):
        batch = items[i:i + BATCH_SIZE]
        results = client.translate(batch, target_language=target_lang, source_language=src_lang)
        translated.extend([r["translatedText"] for r in results])
        print(f"  {label}: {min(i + BATCH_SIZE, total)}/{total}")
    return translated


def print_language_status(script_dir):
    """Show which languages have dictionary files ready and which are still missing."""
    print("\n--- Language status ---")
    for code, name in LANGUAGE_NAMES.items():
        lang_dir = os.path.join(script_dir, code)
        if os.path.isdir(lang_dir):
            json_files = [f for f in os.listdir(lang_dir) if f.endswith(".json")]
            if json_files:
                print(f"  {name:12} ({code})  ready    -> {', '.join(json_files)}")
            else:
                print(f"  {name:12} ({code})  folder exists but no JSON file")
        else:
            print(f"  {name:12} ({code})  MISSING")
    print()


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 translate_dictionary.py <input_json> <language_code>")
        print(f"Supported codes: {', '.join(LANGUAGE_NAMES)}")
        sys.exit(1)

    input_file = sys.argv[1]
    lang_code = sys.argv[2]

    if lang_code not in LANGUAGE_NAMES:
        print(f"Unknown language code '{lang_code}'. Supported: {', '.join(LANGUAGE_NAMES)}")
        sys.exit(1)

    target_language = LANGUAGE_NAMES[lang_code]

    # The source language is inferred from the folder the input file lives in (e.g. en/basic.json -> en)
    src_lang = os.path.basename(os.path.dirname(os.path.abspath(input_file)))
    if src_lang not in LANGUAGE_NAMES:
        print(f"Could not infer source language from folder '{src_lang}'. Supported: {', '.join(LANGUAGE_NAMES)}")
        sys.exit(1)
    src_language = LANGUAGE_NAMES[src_lang]

    # Load the source dictionary
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    entries = data['words']
    words = [e['word'] for e in entries]
    definitions = [e.get('definition', '') for e in entries]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    credentials = load_credentials(script_dir)
    client = translate.Client(credentials=credentials)

    # Translate words
    print(f"Translating {len(words)} words from {src_language} to {target_language}...")
    translated_words = translate_list(client, words, src_lang, lang_code, "words")

    # Only translate definitions that are not empty (most are blank in basic.json)
    non_empty_defs = [(i, d) for i, d in enumerate(definitions) if d]
    translated_definitions = list(definitions)
    if non_empty_defs:
        print(f"Translating {len(non_empty_defs)} definitions...")
        idxs, defs = zip(*non_empty_defs)
        translated = translate_list(client, list(defs), src_lang, lang_code, "definitions")
        for idx, text in zip(idxs, translated):
            translated_definitions[idx] = text

    # Build the output entries: translated word + original word kept as 'translation' for reference
    output_words = []
    for i, entry in enumerate(entries):
        output_words.append({
            "word": translated_words[i],
            "translation": entry['word'],       # original source word for reference in-game
            "definition": translated_definitions[i],
            "etymology": entry.get('etymology', ''),
            "example": entry.get('example', ''),
            "image": entry.get('image', ''),
        })

    # Translate the dictionary name from the source file (e.g. "Basic English Vocabulary" -> "Grundlegender deutscher Wortschatz")
    translated_name = client.translate(data["dictionary_name"], target_language=lang_code, source_language=src_lang)["translatedText"]

    output_data = {
        "dictionary_name": translated_name,
        "words": output_words,
    }

    # Save using the same filename as the input (e.g. en/basic.json -> de/basic.json)
    input_filename = os.path.basename(input_file)
    output_dir = os.path.join(script_dir, lang_code)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, input_filename)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

    print(f"Done. Saved to {output_file}")

    # Show the full status of all languages after the run
    print_language_status(script_dir)


if __name__ == "__main__":
    main()
