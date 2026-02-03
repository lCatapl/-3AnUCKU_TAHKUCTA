from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import db, User, init_admins
from epic_stories import STORIES, TANK_FILTERS
from moderation import mute_user, promote_user
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-tank-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tankist.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    from database import User
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('diary.html')

# ... остальные роуты как раньше ...

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_admins(db)
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))