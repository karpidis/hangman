import secrets
from importlib.resources import files

_openings = None

def _get_openings():
    global _openings
    if _openings is None:
        data = files(__package__).joinpath('chess_openings.txt').read_text()
        _openings = [line for line in data.splitlines() if line]
    return _openings

def generate_password():
    return secrets.choice(_get_openings())
