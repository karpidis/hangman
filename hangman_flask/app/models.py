from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    rating = db.Column(db.Float, nullable=False, default=0.0)
    games = db.relationship('Game', backref='player', lazy=True)

    def __repr__(self):
        return f'<Player {self.username}>'

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(120), unique=True, nullable=False)
    rating = db.Column(db.Float, nullable=False, default=0.0)
    games = db.relationship('Game', backref='word', lazy=True)

    def __repr__(self):
        return f'<Word {self.word}>'

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Game Player: {self.player_id}, Word: {self.word_id}, Score: {self.score}>'