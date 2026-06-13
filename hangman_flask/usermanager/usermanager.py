import sys
from pathlib import Path
from datetime import datetime
import getpass

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pass_generator import main as generate_and_copy_password
from werkzeug.security import generate_password_hash, check_password_hash
from .models import Session, User, UserLanguageStats


def login_or_register():
    """Prompt for username; register new users or authenticate existing ones.
    Returns (user, session)."""
    print("\n=== Hangman ===")
    while True:
        username = input("Enter your username: ").strip().lower()
        if not username:
            print("Username cannot be empty.")
        elif " " in username:
            print("Username cannot contain spaces.")
        else:
            break

    session = Session()
    user = session.query(User).filter_by(username=username).first()

    if user is None:
        _register(username, session)
        user = session.query(User).filter_by(username=username).first()
    else:
        _login(user, session)

    return user, session


def get_or_create_language_stats(user, session, language_id: int) -> UserLanguageStats:
    """Return the user's stats for a language, creating the row if it's the first time."""
    stats = session.query(UserLanguageStats).filter_by(
        user_id=user.id, language_id=language_id
    ).first()
    if not stats:
        stats = UserLanguageStats(user_id=user.id, language_id=language_id)
        session.add(stats)
        session.commit()
    return stats


def update_stats(user, session, language_id: int, score: int, streak: int, elo_delta: float = 0.0):
    """Update per-language stats after a session."""
    stats = get_or_create_language_stats(user, session, language_id)
    if score > stats.high_score:
        stats.high_score = score
    if streak > stats.best_streak:
        stats.best_streak = streak
    stats.elo = max(0, round(stats.elo + elo_delta))
    session.commit()


def _register(username, session):
    print(f"\nNo account found for '{username}'. Let's create one.")
    email = _prompt_email(session)

    password = generate_and_copy_password()
    print("Save it — it will not be shown again.\n")

    new_user = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
        date_joined=datetime.utcnow(),
    )
    session.add(new_user)
    session.commit()
    print(f"Account created! Welcome, {username}!\n")


def _login(user, session):
    for attempt in range(3):
        password = getpass.getpass("Password: ")
        if check_password_hash(user.password, password):
            print(f"\nWelcome back, {user.username}!")
            # Show stats across all languages the user has played
            all_stats = session.query(UserLanguageStats).filter_by(user_id=user.id).all()
            if all_stats:
                best_elo = max(s.elo for s in all_stats)
                print(f"Best ELO across all languages: {best_elo}")
            print()
            return
        remaining = 2 - attempt
        if remaining > 0:
            print(f"Wrong password. {remaining} attempt(s) left.")
        else:
            print("Too many failed attempts. Exiting.")
            session.close()
            sys.exit(1)


def _prompt_email(session):
    while True:
        email = input("Enter your email address: ").strip()
        if "@" not in email or "." not in email:
            print("Please enter a valid email address.")
            continue
        if session.query(User).filter_by(email=email).first():
            print("That email is already registered. Please use a different one.")
            continue
        return email
