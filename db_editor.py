import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
import os
import threading
from typing import Optional, List, Tuple
from deepseek_client import DeepseekClient
import sys

# Setup logging to file
LOG_FILE = "db_editor.log"
def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{msg}\n")
    print(msg, file=sys.stderr)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_ROOT = os.path.join(BASE_DIR, "db")
MAIN_DB = os.path.join(DB_ROOT, "Main.db")


class DBEditor:
    def __init__(self, root):
        # Clear log file
        with open(LOG_FILE, "w") as f:
            f.write("=== DB Editor Log ===\n")

        log("DBEditor initialized")
        self.root = root
        self.root.title("Hangman Dictionary Editor")
        self.root.geometry("1200x800")

        self.main_db_con = None
        self.lang_db_con = None
        self.deepseek = None
        self.current_word_id = None
        self.words_cache = []
        self.current_page = 0
        self.page_size = 20
        self.enrichment_running = False
        self.is_new_word = False

        try:
            self.deepseek = DeepseekClient()
        except ValueError as e:
            messagebox.showerror("Deepseek Error", str(e))
            self.deepseek = None

        self.setup_ui()
        self.load_languages()

    def setup_ui(self):
        # Top frame: Language and Dictionary selection
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top_frame, text="Language:").pack(side=tk.LEFT, padx=5)
        self.language_var = tk.StringVar()
        self.language_combo = ttk.Combobox(top_frame, textvariable=self.language_var, state="readonly", width=20)
        self.language_combo.pack(side=tk.LEFT, padx=5)
        self.language_combo.bind("<<ComboboxSelected>>", lambda e: self.on_language_changed())

        ttk.Label(top_frame, text="Dictionary:").pack(side=tk.LEFT, padx=5)
        self.dictionary_var = tk.StringVar()
        self.dictionary_combo = ttk.Combobox(top_frame, textvariable=self.dictionary_var, state="readonly", width=20)
        self.dictionary_combo.pack(side=tk.LEFT, padx=5)
        self.dictionary_combo.bind("<<ComboboxSelected>>", lambda e: self.on_dictionary_changed())

        # Search frame
        search_frame = ttk.Frame(self.root)
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self.search_words())

        ttk.Button(search_frame, text="Clear", command=self.clear_search).pack(side=tk.LEFT, padx=5)

        # Main content frame
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel: Word list
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))

        ttk.Label(left_frame, text="Words").pack()

        # Word list with scrollbar
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.word_listbox = tk.Listbox(list_frame, width=25, yscrollcommand=scrollbar.set, exportselection=False)
        self.word_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.word_listbox.bind("<<ListboxSelect>>", lambda e: self.on_word_selected())
        scrollbar.config(command=self.word_listbox.yview)

        # Pagination buttons
        page_frame = ttk.Frame(left_frame)
        page_frame.pack(fill=tk.X, pady=5)

        ttk.Button(page_frame, text="◀ Prev", command=self.prev_page).pack(side=tk.LEFT, padx=2)
        self.page_label = ttk.Label(page_frame, text="Page 1")
        self.page_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(page_frame, text="Next ▶", command=self.next_page).pack(side=tk.LEFT, padx=2)

        # Right panel: Word editor
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.editor_title = ttk.Label(right_frame, text="Edit Word")
        self.editor_title.pack()

        # Editor fields
        fields_frame = ttk.Frame(right_frame)
        fields_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        fields = [
            ("Word:", "word", False),
            ("Translation:", "translation", False),
            ("Definition:", "definition", True),
            ("Etymology:", "etymology", True),
            ("Example:", "example", True),
            ("Image URL:", "image", False),
        ]

        self.field_widgets = {}

        for label, key, is_multiline in fields:
            ttk.Label(fields_frame, text=label).pack(anchor=tk.W, pady=(10, 0))

            if is_multiline:
                widget = scrolledtext.ScrolledText(fields_frame, height=3, width=50, wrap=tk.WORD)
                widget.pack(fill=tk.X, pady=5)
            else:
                widget = ttk.Entry(fields_frame)
                widget.pack(fill=tk.X, pady=5)

            self.field_widgets[key] = widget

        # Buttons frame
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="New Word", command=self.new_word).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save", command=self.save_word).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Discard", command=self.discard_changes).pack(side=tk.LEFT, padx=5)

        # Enrichment frame
        enrichment_frame = ttk.LabelFrame(right_frame, text="Deepseek Enrichment", padding=10)
        enrichment_frame.pack(fill=tk.X, pady=10)

        scope_frame = ttk.Frame(enrichment_frame)
        scope_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(scope_frame, text="Scope:").pack(side=tk.LEFT, padx=(0, 5))
        self.enrichment_scope_var = tk.StringVar(value="search")
        ttk.Radiobutton(
            scope_frame,
            text="Search word",
            variable=self.enrichment_scope_var,
            value="search"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            scope_frame,
            text="All missing",
            variable=self.enrichment_scope_var,
            value="all"
        ).pack(side=tk.LEFT, padx=5)

        self.fetch_definitions_button = ttk.Button(
            enrichment_frame,
            text="Fetch Definitions",
            command=self.fetch_missing_definitions
        )
        self.fetch_definitions_button.pack(fill=tk.X, pady=5)
        self.fetch_etymologies_button = ttk.Button(
            enrichment_frame,
            text="Fetch Etymologies",
            command=self.fetch_missing_etymologies
        )
        self.fetch_etymologies_button.pack(fill=tk.X, pady=5)

        self.progress_label = ttk.Label(enrichment_frame, text="")
        self.progress_label.pack(fill=tk.X, pady=5)

    def load_languages(self):
        """Load languages from Main.db."""
        try:
            con = sqlite3.connect(MAIN_DB)
            con.row_factory = sqlite3.Row
            rows = con.execute("SELECT id, name, code FROM languages ORDER BY name").fetchall()
            con.close()

            self.languages = {row["name"]: (row["id"], row["code"]) for row in rows}
            self.language_combo["values"] = list(self.languages.keys())

            if self.languages:
                self.language_combo.current(0)
                self.on_language_changed()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load languages: {e}")

    def on_language_changed(self):
        """Update dictionaries when language changes."""
        lang_name = self.language_var.get()
        if not lang_name:
            return

        lang_id, lang_code = self.languages[lang_name]

        try:
            con = sqlite3.connect(MAIN_DB)
            con.row_factory = sqlite3.Row
            rows = con.execute(
                "SELECT id, dictionary_name FROM dictionaries WHERE language_id = ? ORDER BY dictionary_name",
                (lang_id,)
            ).fetchall()
            con.close()

            self.dictionaries = {row["dictionary_name"]: row["id"] for row in rows}
            self.dictionary_combo["values"] = list(self.dictionaries.keys())

            if self.dictionaries:
                self.dictionary_combo.current(0)
                self.on_dictionary_changed()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load dictionaries: {e}")

    def on_dictionary_changed(self):
        """Load language database and refresh word list."""
        lang_name = self.language_var.get()
        dict_name = self.dictionary_var.get()

        if not lang_name or not dict_name:
            return

        lang_id, lang_code = self.languages[lang_name]
        dict_id = self.dictionaries[dict_name]

        db_path = os.path.join(DB_ROOT, lang_code, f"{lang_name}.db")

        if self.lang_db_con:
            self.lang_db_con.close()

        try:
            self.lang_db_con = sqlite3.connect(db_path)
            self.lang_db_con.row_factory = sqlite3.Row
            self.current_dictionary_id = dict_id
            self.current_page = 0
            self.load_words()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open database: {e}")

    def load_words(self, auto_select: bool = True):
        """Load words for current page."""
        if not self.lang_db_con:
            return

        try:
            search_term = self.search_var.get()
            if search_term:
                query = "SELECT id, word FROM words WHERE dictionary_id = ? AND word LIKE ? ORDER BY word"
                params = (self.current_dictionary_id, f"{search_term}%")
            else:
                query = "SELECT id, word FROM words WHERE dictionary_id = ? ORDER BY word"
                params = (self.current_dictionary_id,)

            all_words = self.lang_db_con.execute(query, params).fetchall()
            self.words_cache = all_words

            start_idx = self.current_page * self.page_size
            end_idx = start_idx + self.page_size
            page_words = self.words_cache[start_idx:end_idx]

            self.word_listbox.delete(0, tk.END)
            for row in page_words:
                self.word_listbox.insert(tk.END, row["word"])

            total_pages = (len(self.words_cache) + self.page_size - 1) // self.page_size
            self.page_label.config(text=f"Page {self.current_page + 1}/{max(1, total_pages)}")

            if page_words and auto_select:
                self.word_listbox.selection_set(0)
                self.word_listbox.activate(0)
                self.load_word_details(page_words[0]["id"])
            elif not page_words:
                self.clear_editor()
                self.editor_title.config(text="No Words Found")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load words: {e}")

    def search_words(self):
        """Filter words based on search input."""
        self.current_page = 0
        self.load_words()

    def clear_search(self):
        """Clear search and reload all words."""
        self.search_var.set("")
        self.search_words()

    def prev_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_words()

    def next_page(self):
        """Go to next page."""
        max_page = (len(self.words_cache) + self.page_size - 1) // self.page_size
        if self.current_page < max_page - 1:
            self.current_page += 1
            self.load_words()

    def on_word_selected(self):
        """Load selected word into editor."""
        selection = self.word_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        page_start = self.current_page * self.page_size
        word_idx = page_start + idx

        if word_idx < len(self.words_cache):
            word_id = self.words_cache[word_idx]["id"]
            self.load_word_details(word_id)

    def load_word_details(self, word_id: int):
        """Load word details from database."""
        try:
            row = self.lang_db_con.execute(
                "SELECT word, translation, definition, etymology, example, image FROM words WHERE id = ?",
                (word_id,)
            ).fetchone()

            if row:
                self.current_word_id = word_id
                self.is_new_word = False
                self.editor_title.config(text=f"Edit Word: {row['word']}")
                self.set_entry_value("word", row["word"] or "", disabled=True)

                for key in ["translation", "definition", "etymology", "example", "image"]:
                    self.set_field_value(key, row[key] or "")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load word details: {e}")

    def set_field_value(self, key: str, value: str):
        widget = self.field_widgets[key]
        if isinstance(widget, scrolledtext.ScrolledText):
            widget.delete("1.0", tk.END)
            widget.insert("1.0", value)
        else:
            widget.delete(0, tk.END)
            widget.insert(0, value)

    def set_entry_value(self, key: str, value: str, disabled: bool = False):
        widget = self.field_widgets[key]
        widget.config(state=tk.NORMAL)
        widget.delete(0, tk.END)
        widget.insert(0, value)
        if disabled:
            widget.config(state=tk.DISABLED)

    def clear_editor(self):
        self.current_word_id = None
        self.is_new_word = False
        self.editor_title.config(text="Edit Word")
        self.set_entry_value("word", "", disabled=True)

        for key in ["translation", "definition", "etymology", "example", "image"]:
            self.set_field_value(key, "")

    def new_word(self):
        """Prepare the editor to create a new word in the current dictionary."""
        if not self.lang_db_con:
            messagebox.showwarning("Warning", "Select a language and dictionary first.")
            return

        self.word_listbox.selection_clear(0, tk.END)
        self.current_word_id = None
        self.is_new_word = True
        self.editor_title.config(text="New Word")
        self.set_entry_value("word", "", disabled=False)

        for key in ["translation", "definition", "etymology", "example", "image"]:
            self.set_field_value(key, "")

        self.field_widgets["word"].focus_set()

    def save_word(self):
        """Save changes to database."""
        if not self.current_word_id and not self.is_new_word:
            messagebox.showwarning("Warning", "Select a word from the list or click New Word first.")
            return

        try:
            word = self.field_widgets["word"].get().strip()
            if self.is_new_word and not word:
                messagebox.showwarning("Warning", "Enter a word before saving.")
                return

            values = {}
            for key in ["translation", "definition", "etymology", "example", "image"]:
                widget = self.field_widgets[key]
                if isinstance(widget, scrolledtext.ScrolledText):
                    values[key] = widget.get("1.0", tk.END).strip()
                else:
                    values[key] = widget.get().strip()

            if self.is_new_word:
                cursor = self.lang_db_con.execute(
                    """INSERT INTO words
                       (dictionary_id, word, translation, definition, etymology, example, image)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (self.current_dictionary_id, word, values["translation"], values["definition"],
                     values["etymology"], values["example"], values["image"])
                )
                self.current_word_id = cursor.lastrowid
                self.is_new_word = False
            else:
                self.lang_db_con.execute(
                    """UPDATE words SET translation = ?, definition = ?, etymology = ?, example = ?, image = ?
                       WHERE id = ?""",
                    (values["translation"], values["definition"], values["etymology"],
                     values["example"], values["image"], self.current_word_id)
                )

            self.lang_db_con.commit()
            saved_word_id = self.current_word_id
            self.load_words(auto_select=False)
            if not self.select_word_by_id(saved_word_id):
                self.load_word_details(saved_word_id)
            messagebox.showinfo("Success", "Word saved successfully.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save word: {e}")

    def discard_changes(self):
        """Discard changes and reload from database."""
        if self.current_word_id:
            self.load_word_details(self.current_word_id)
        elif self.is_new_word:
            self.clear_editor()

    def select_word_by_id(self, word_id: int):
        """Select a word in the current cached page when it is visible."""
        page_start = self.current_page * self.page_size
        page_end = page_start + self.page_size

        for list_idx, row in enumerate(self.words_cache[page_start:page_end]):
            if row["id"] == word_id:
                self.word_listbox.selection_clear(0, tk.END)
                self.word_listbox.selection_set(list_idx)
                self.word_listbox.activate(list_idx)
                self.word_listbox.see(list_idx)
                self.load_word_details(word_id)
                return True

        return False

    def _get_search_word_rows(self) -> List[Tuple[int, str]]:
        """Return the single word identified by the current search text."""
        if not self.lang_db_con:
            messagebox.showwarning("Warning", "Select a language and dictionary first.")
            return []

        search_term = self.search_var.get().strip()
        if not search_term:
            messagebox.showwarning("Warning", "Type the word in Search first.")
            return []

        exact_rows = self.lang_db_con.execute(
            """SELECT id, word FROM words
               WHERE dictionary_id = ? AND LOWER(word) = LOWER(?)
               ORDER BY word""",
            (self.current_dictionary_id, search_term)
        ).fetchall()

        if exact_rows:
            return [(exact_rows[0]["id"], exact_rows[0]["word"])]

        prefix_rows = self.lang_db_con.execute(
            """SELECT id, word FROM words
               WHERE dictionary_id = ? AND word LIKE ?
               ORDER BY word
               LIMIT 2""",
            (self.current_dictionary_id, f"{search_term}%")
        ).fetchall()

        if len(prefix_rows) == 1:
            return [(prefix_rows[0]["id"], prefix_rows[0]["word"])]

        if prefix_rows:
            messagebox.showwarning("Warning", "More than one word matches Search. Type the exact word.")
        else:
            messagebox.showinfo("Not Found", f"No word found for '{search_term}'.")

        return []

    def _get_missing_word_rows(self, field_type: str) -> List[Tuple[int, str]]:
        """Return all words missing the requested enrichment field."""
        if not self.lang_db_con:
            messagebox.showwarning("Warning", "Select a language and dictionary first.")
            return []

        field = "definition" if field_type == "definitions" else "etymology"
        rows = self.lang_db_con.execute(
            f"""SELECT id, word FROM words
                WHERE dictionary_id = ? AND ({field} IS NULL OR TRIM({field}) = '')
                ORDER BY word""",
            (self.current_dictionary_id,)
        ).fetchall()

        if not rows:
            messagebox.showinfo("No Missing Words", f"No words are missing {field_type}.")
            return []

        return [(row["id"], row["word"]) for row in rows]

    def _get_enrichment_word_rows(self, field_type: str) -> List[Tuple[int, str]]:
        if self.enrichment_scope_var.get() == "all":
            return self._get_missing_word_rows(field_type)

        return self._get_search_word_rows()

    def fetch_missing_definitions(self):
        """Fetch missing definitions from deepseek."""
        log("fetch_missing_definitions clicked")
        if not self.deepseek:
            log("ERROR: Deepseek not initialized")
            messagebox.showerror("Error", "Deepseek client not initialized.")
            return

        row_data = self._get_enrichment_word_rows("definitions")
        if row_data:
            self._start_enrichment_thread("definitions", row_data)

    def _set_enrichment_buttons_state(self, state: str):
        self.fetch_definitions_button.config(state=state)
        self.fetch_etymologies_button.config(state=state)

    def _set_progress(self, text: str):
        self.progress_label.config(text=text)

    def _start_enrichment_thread(self, field_type: str, word_rows: List):
        """Start enrichment work without blocking the tkinter event loop."""
        if self.enrichment_running:
            messagebox.showwarning("Enrichment Running", "Please wait for the current enrichment to finish.")
            return

        if not word_rows:
            messagebox.showinfo("No Word", f"No word selected for {field_type}.")
            return

        lang_name = self.language_var.get()
        lang_id, lang_code = self.languages[lang_name]
        db_path = os.path.join(DB_ROOT, lang_code, f"{lang_name}.db")

        self.enrichment_running = True
        self._set_enrichment_buttons_state(tk.DISABLED)
        self._set_progress(f"Starting {field_type} enrichment for {len(word_rows)} words...")
        log(f"Starting thread for {field_type} with {len(word_rows)} words")

        worker = threading.Thread(
            target=self._fetch_enrichment_worker,
            args=(field_type, word_rows, lang_name, db_path),
            daemon=True
        )
        worker.start()

    def _fetch_enrichment_worker(self, field_type: str, word_rows: List, lang_name: str, db_path: str):
        """Fetch enrichment data in a background thread."""
        try:
            log(f"Starting enrichment for {field_type} with {len(word_rows)} words")
            log(f"DB path: {db_path}")

            results = []

            for idx, (word_id, word) in enumerate(word_rows):
                msg = f"Fetching {field_type}... {idx + 1}/{len(word_rows)}"
                log(msg)
                self.root.after(0, self._set_progress, msg)

                if field_type == "definitions":
                    enriched = self.deepseek.get_definition(word, lang_name)
                else:
                    enriched = self.deepseek.get_etymology(word, lang_name)

                if enriched:
                    results.append((word_id, word, enriched))
                    log(f"✓ {word}: {enriched[:50]}...")

            log(f"Got {len(results)}/{len(word_rows)} results")
            self.root.after(
                0,
                self._finish_enrichment,
                field_type,
                results,
                db_path,
                len(word_rows),
                None
            )

        except Exception as e:
            log(f"Error: {e}")
            import traceback
            log(traceback.format_exc())
            self.root.after(
                0,
                self._finish_enrichment,
                field_type,
                [],
                db_path,
                len(word_rows),
                e
            )

    def _finish_enrichment(self, field_type: str, results: List[Tuple], db_path: str, total: int, error: Optional[Exception]):
        """Finish enrichment on the tkinter thread."""
        self.enrichment_running = False
        self._set_enrichment_buttons_state(tk.NORMAL)

        if error:
            self._set_progress(f"Error fetching {field_type}.")
            messagebox.showerror("Error", f"Failed to fetch {field_type}: {error}")
            return

        self._set_progress(f"Fetched {len(results)}/{total} {field_type}.")

        if results:
            self._show_results_approval(field_type, results, db_path)
        else:
            messagebox.showwarning("No Results", f"Failed to fetch any {field_type}.")

    def _show_results_approval(self, field_type: str, results: List[Tuple], db_path: str):
        """Show approval dialog with results before saving."""
        result_window = tk.Toplevel(self.root)
        result_window.title(f"Enrichment Results - Approve & Save")
        result_window.geometry("700x500")

        ttk.Label(result_window, text=f"Fetched {len(results)} {field_type}. Review and save:",
                  font=("", 10, "bold")).pack(pady=10)

        # Results list with scrollbar
        list_frame = ttk.Frame(result_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)

        text_widget = scrolledtext.ScrolledText(list_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)

        # Display results
        for word_id, word, enriched_text in results:
            text_widget.insert(tk.END, f"[{word}]\n{enriched_text}\n\n", "word")

        text_widget.tag_config("word", font=("", 9, "bold"))
        text_widget.config(state=tk.DISABLED)

        # Buttons
        button_frame = ttk.Frame(result_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def save_results():
            try:
                con = sqlite3.connect(db_path)
                field = "definition" if field_type == "definitions" else "etymology"

                for word_id, word, enriched_text in results:
                    con.execute(
                        f"UPDATE words SET {field} = ? WHERE id = ?",
                        (enriched_text, word_id)
                    )

                con.commit()
                con.close()
                result_window.destroy()
                messagebox.showinfo("Success", f"Saved {len(results)} {field_type} to database.")
                self.progress_label.config(text=f"Saved {len(results)} {field_type}.")
                if self.current_word_id in [word_id for word_id, word, enriched_text in results]:
                    self.load_word_details(self.current_word_id)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")

        ttk.Button(button_frame, text="Cancel", command=result_window.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text=f"Save All ({len(results)})", command=save_results).pack(side=tk.LEFT, padx=5)

    def fetch_missing_etymologies(self):
        """Fetch missing etymologies from deepseek."""
        if not self.deepseek:
            messagebox.showerror("Error", "Deepseek client not initialized.")
            return

        row_data = self._get_enrichment_word_rows("etymologies")
        if row_data:
            self._start_enrichment_thread("etymologies", row_data)

    def __del__(self):
        """Cleanup database connections."""
        if self.main_db_con:
            self.main_db_con.close()
        if self.lang_db_con:
            self.lang_db_con.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = DBEditor(root)
    root.mainloop()
