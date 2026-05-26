#Create a users.db database and a users table with the following columns: id (integer primary key), username (text), email (text), and password (text).
from sqlalchemy import create_engine, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE_URL = "sqlite:///Hangman Terminal Version 1/usermanager/users.db"
engine = create_engine(DATABASE_URL)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(256))
    plays: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    high_score: Mapped[int] = mapped_column(Integer, default=0)
    elo: Mapped[int] = mapped_column(Integer, default=1000)
    date_joined: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(engine)