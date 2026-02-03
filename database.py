from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default="Start")
    muted_until = db.Column(db.DateTime, nullable=True)
    muted_reason = db.Column(db.String(200))
    muted_by_id = db.Column(db.Integer)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class UserNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    note = db.Column(db.Text, nullable=False)
    tank_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def init_admins(db):
    """Создаёт админов если их нет"""
    if not User.query.filter_by(username="Назар").first():
        nazar = User(username="Назар", email="nazartrahov1@gmail.com",
                    password_hash=generate_password_hash("120187"), role="Admin")
        catnap = User(username="CatNap", email="catnap@example.com",
                     password_hash=generate_password_hash("120187"), role="Admin")
        db.session.add_all([nazar, catnap])
        db.session.commit()