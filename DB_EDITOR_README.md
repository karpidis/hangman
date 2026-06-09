# Dictionary Database Editor & Enricher

A tkinter-based GUI application for browsing, editing, and enriching dictionary entries with definitions and etymologies using the Deepseek API.

## Features

- **Browse & Edit**: Browse all dictionary entries and edit any field (translation, definition, etymology, example, image URL)
- **Search**: Filter words by prefix or contains search
- **Deepseek Integration**: Auto-fill missing definitions and etymologies using the Deepseek API
- **Multi-language Support**: Work with any language in the database
- **Pagination**: Navigate large dictionaries with page-based browsing
- **Threading**: Background API calls keep the UI responsive

## Setup

### 1. Install Dependencies

```bash
pip install requests python-dotenv
```

These are already included in most Python environments, but ensure they're available.

### 2. Configure Deepseek API Key

Edit `.env` in the project root:

```env
DEEPSEEK_API_KEY=your_actual_api_key_here
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=30
```

Get your API key from [Deepseek](https://platform.deepseek.com).

### 3. Run the Application

```bash
python db_editor.py
```

## Usage

### Browse & Edit Entries

1. Select a **Language** from the dropdown
2. Select a **Dictionary** for that language
3. Use **Search** to find words (optional)
4. Click a word in the list to load it
5. Edit any field in the right panel
6. Click **Save** to persist changes

### Enrich Missing Data

1. Select a language and dictionary
2. Click **"Fetch Missing Definitions"** to fill in NULL definition fields
3. Click **"Fetch Missing Etymologies"** to fill in NULL etymology fields
4. Monitor progress in the progress label
5. Changes are saved automatically to the database

### Tips

- The editor shows up to 20 words per page by default (paginate with Previous/Next)
- Use the search box to filter by word prefix (e.g., "ab" finds "abandon", "ability")
- Press **Discard** to reload the current word from the database without saving
- The word field itself is read-only to prevent accidental changes
- API calls run in background threads so the UI stays responsive

## Database Schema

**Words table** (`db/{language_code}/{language_name}.db`):
- `id`: Primary key
- `dictionary_id`: Foreign key to Main.db dictionaries table
- `word`: The word string
- `translation`: Translated word/phrase
- `definition`: English definition
- `etymology`: Word origin/history
- `example`: Usage example
- `image`: Image URL or path

## Architecture

### Files

- **db_editor.py**: Main tkinter application with UI and database logic
- **deepseek_client.py**: Deepseek API client with retry logic
- **.env**: Configuration file (add to .gitignore)

### Database Connections

- **Main.db**: Read-only central database with language/dictionary registry
- **db/{lang_code}/{lang_name}.db**: Language-specific database with word entries

### Threading

Deepseek API calls run in background threads to prevent UI freezing. Progress updates are sent back to the main thread.

## Error Handling

- **Missing API Key**: Application warns at startup if DEEPSEEK_API_KEY is not set
- **Network Errors**: API client retries up to 2 times on network failures
- **Rate Limiting**: Gracefully handles 429 responses from Deepseek
- **Timeouts**: 30-second timeout per API call (configurable)

## Troubleshooting

**"DEEPSEEK_API_KEY not found"**
- Ensure `.env` file exists in the project root with your valid API key

**"Database not found"**
- Ensure you've selected both a language and dictionary
- Check that the database files exist in the `db/` directory

**Slow API calls**
- Deepseek API response times vary; increase DEEPSEEK_TIMEOUT in .env if needed
- Consider enriching smaller batches (filter by search first)

**UI not responding during batch enrichment**
- This is expected; batch operations run in background threads
- The progress label shows current progress
- Wait for the completion dialog to appear

## Future Enhancements

- Export/import word lists as CSV
- Undo/redo functionality
- Batch editing capabilities
- Dictionary comparison view
- Word statistics and usage analytics
