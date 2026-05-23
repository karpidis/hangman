#Create a users.db database and a users table with the following columns: id (integer primary key), username (text), email (text), and password (text).
from sqlalchemy import create_engine, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

DATABASE_URL = "sqlite:///users.db"
engine = create_engine(DATABASE_URL)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    plays: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    high_score: Mapped[int] = mapped_column(Integer, default=0)
    elo: Mapped[int] = mapped_column(Integer, default=1000)
    date_joined: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    def __init__(self, id, username, email, password, plays=0, 
                 wins=0, high_score=0, elo=1000
                 ):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.plays = plays
        self.wins = wins
        self.high_score = high_score
        self.elo = elo
       


Base.metadata.create_all(engine)