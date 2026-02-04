from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
import json
import os
from datetime import datetime
from functools import wraps
import hashlib

app = Flask(__name__)
app.secret_key = 'tank-battalion-2026-super-secret-key-change-in-production'

# ========== ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect('tanks.db')
    c = conn.cursor()
    
    # Чат
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT NOT NULL, 
                  message TEXT NOT NULL, 
                  timestamp TEXT NOT NULL)''')
    
    # Заметки танкиста
    c.execute('''CREATE TABLE IF NOT EXISTS notes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT NOT NULL, 
                  content TEXT NOT NULL, 
                  timestamp TEXT NOT NULL)''')
    
    # Пользователи (если используешь login/register)
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  email TEXT,
                  created_at TEXT)''')
    
    # Лидерборд (очки)
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL,
                  score INTEGER DEFAULT 0,
                  updated_at TEXT)''')
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована!")

init_db()

# ========== ДЕКОРАТОРЫ ==========
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Войдите в бой!', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ========== ГЛАВНАЯ СТРАНИЦА ==========
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'username' in request.form:
            session['username'] = request.form['username'][:20] or 'Танкист'
    
    return render_template('index.html')

# ========== ЧАТ ==========
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        username = session.get('username', 'Танкист')
        message = request.form.get('message', '').strip()[:200]
        
        if message:
            timestamp = datetime.now().strftime('%H:%M')
            
            conn = sqlite3.connect('tanks.db')
            c = conn.cursor()
            c.execute("INSERT INTO messages (username, message, timestamp) VALUES (?, ?, ?)",
                      (username, message, timestamp))
            conn.commit()
            conn.close()
            return jsonify({'status': 'ok'})
    
    # GET - загрузка сообщений
    conn = sqlite3.connect('tanks.db')
    c = conn.cursor()
    c.execute("SELECT username, message, timestamp FROM messages ORDER BY id DESC LIMIT 50")
    messages = c.fetchall()
    conn.close()
    
    return jsonify({'messages': messages[::-1]})  # Новые сверху

# ========== ЗАМЕТКИ ==========
@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'POST':
        title = request.form.get('title', 'Без названия')[:50]
        content = request.form.get('content', '').strip()[:1000]
        
        if content:
            timestamp = datetime.now().strftime('%H:%M')
            
            conn = sqlite3.connect('tanks.db')
            c = conn.cursor()
            c.execute("INSERT INTO notes (title, content, timestamp) VALUES (?, ?, ?)",
                      (title, content, timestamp))
            conn.commit()
            conn.close()
            return jsonify({'status': 'ok'})
    
    # GET - загрузка заметок
    conn = sqlite3.connect('tanks.db')
    c = conn.cursor()
    c.execute("SELECT title, content, timestamp FROM notes ORDER BY id DESC LIMIT 20")
    notes_list = c.fetchall()
    conn.close()
    
    return jsonify({'notes': notes_list})

# ========== АВТОРИЗАЦИЯ ==========
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        conn = sqlite3.connect('tanks.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['username'] = username
            flash('Добро пожаловать в бой, командир!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный логин/пароль', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        email = request.form.get('email', '')
        
        try:
            conn = sqlite3.connect('tanks.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password, email, created_at) VALUES (?, ?, ?, ?)",
                      (username, password, email, datetime.now().strftime('%Y-%m-%d %H:%M')))
            conn.commit()
            conn.close()
            flash('Аккаунт создан! Войдите в бой.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Пользователь уже существует', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Вы покинули поле боя', 'info')
    return redirect(url_for('index'))

# ========== ЛИДЕРБОРД ==========
@app.route('/leaderboard')
def leaderboard():
    conn = sqlite3.connect('tanks.db')
    c = conn.cursor()
    c.execute("SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10")
    top_players = c.fetchall()
    conn.close()
    
    return jsonify({'leaderboard': top_players})

# ========== ПРОЧИЕ СТРАНИЦЫ (оставляем твои) ==========
@app.route('/chat')
def chat_page():
    return render_template('chat.html')

@app.route('/diary')
def diary():
    return render_template('diary.html')

@app.route('/leaderboard')
def leaderboard_page():
    return render_template('leaderboard.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/tanks')
def tanks():
    return render_template('tanks.html')

# ========== API для мобильных/фронтенда ==========
@app.route('/api/tanks')
def api_tanks():
    try:
        with open('static/tanks.json', 'r', encoding='utf-8') as f:
            tanks = json.load(f)
        return jsonify(tanks)
    except:
        return jsonify({"error": "Танки не найдены"}), 404

# ========== ОШИБКИ ==========
@app.errorhandler(404)
def not_found(error):
    return render_template('base.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return "Ошибка сервера. Проверь логи.", 500

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("🚀 Tank Battalion запускается на http://localhost:5000")
    print("📁 База: tanks.db")
    app.run(debug=True, host='0.0.0.0', port=5000)
