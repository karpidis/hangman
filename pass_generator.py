import subprocess
import sys
from chess_passgen import generate_password

def copy_to_clipboard(text):
    if sys.platform == 'win32':
        subprocess.run(['clip'], input=text.encode(), check=True)
    elif sys.platform == 'darwin':
        subprocess.run(['pbcopy'], input=text.encode(), check=True)
    else:
        try:
            subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode(), check=True)
        except FileNotFoundError:
            try:
                subprocess.run(['xsel', '--clipboard', '--input'], input=text.encode(), check=True)
            except FileNotFoundError:
                import tkinter as tk
                root = tk.Tk()
                root.withdraw()
                root.clipboard_clear()
                root.clipboard_append(text)
                root.update()
                root.after(5000, root.destroy)
                root.mainloop()

def main():
    password = generate_password()
    copy_to_clipboard(password)
    print(f"Password copied to clipboard: {password}")
    return password

if __name__ == "__main__":
    main()
