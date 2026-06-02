from pathlib import Path
from sqlalchemy import create_engine, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, relationship
from datetime import datetime

# Local user database — created on first run, never shipped with the app
DB_PATH = Path(__file__).resolve().parent.parent / "db" / "users.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(256))
    date_joined: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    stats: Mapped[list["UserLanguageStats"]] = relationship("UserLanguageStats", back_populates="user")


class UserLanguageStats(Base):
    __tablename__ = "user_language_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    language_id: Mapped[int] = mapped_column(Integer)
    elo: Mapped[int] = mapped_column(Integer, default=1000)
    high_score: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship("User", back_populates="stats")


Base.metadata.create_all(engine)  # creates users.db tables on first run; safe to call every time
