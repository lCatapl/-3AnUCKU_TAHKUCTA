from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
import hashlib
import random
import json
from datetime import datetime
from werkzeug.routing import BaseConverter

app = Flask(__name__)
app.secret_key = 'tank-battalion-2026-v2'

# АДМИНЫ (пароли НЕ видны!)
ADMIN_USERS = {'CatNap': '120187', 'Назар': '120187'}

def init_db():
    conn = sqlite3.connect('tanks.db', check_same_thread=False)
    c = conn.cursor()
    
    # ОСНОВНЫЕ ТАБЛИЦЫ
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, message TEXT, timestamp TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS notes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT, timestamp TEXT, username TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, created_at TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard 
                 (username TEXT PRIMARY KEY, score INTEGER DEFAULT 0, updated_at TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS garage 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, tank_name TEXT, bought_at TEXT)''')
    
    # ТЕСТОВЫЕ ДАННЫЕ
    c.execute("INSERT OR IGNORE INTO users (username, password, created_at) VALUES ('test', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', ?)", 
              (datetime.now().strftime('%Y-%m-%d'),))
    c.execute("INSERT OR IGNORE INTO leaderboard (username, score, updated_at) VALUES ('test', 1000, ?)", 
              (datetime.now().strftime('%Y-%m-%d %H:%M'),))
    
    conn.commit()
    conn.close()

# ЗВАНИЯ
def get_rank(score):
    ranks = {0:"🪖 Новобранец", 100:"🔫 Рядовой", 1000:"⭐ Капрал", 5000:"⚔️ Сержант", 
             25000:"🎖️ Старшина", 100000:"👑 Лейтенант", 500000:"🏆 Капитан", 1000000:"🔥 Ветеран"}
    for threshold, rank_name in sorted(ranks.items(), reverse=True):
        if score >= threshold: return rank_name
    return "🪖 Новобранец"

def update_score(username, points):
    conn = sqlite3.connect('tanks.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO leaderboard (username, score, updated_at) VALUES (?, COALESCE((SELECT score FROM leaderboard WHERE username=?), 0)+?, ?)",
              (username, username, points, datetime.now().strftime('%Y-%m-%d %H:%M')))
    conn.commit()
    conn.close()

init_db()

# ===== ОСНОВНЫЕ РОУТЫ =====
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        # АДМИНЫ
        if username in ADMIN_USERS and ADMIN_USERS[username] == password:
            session['username'] = username
            session['is_admin'] = True
            flash('🔥 Админ-доступ активирован!', 'success')
            return redirect('/')
        
        # ОБЫЧНЫЕ
        conn = sqlite3.connect('tanks.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", 
                  (username, hashlib.sha256(password.encode()).hexdigest()))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['username'] = username
            flash('✅ Добро пожаловать в бой!', 'success')
            return redirect('/')
        flash('❌ Неверный логин/пароль', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        conn = sqlite3.connect('tanks.db', check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
                     (username, hashlib.sha256(password.encode()).hexdigest(), datetime.now().strftime('%Y-%m-%d')))
            conn.commit()
            flash('✅ Регистрация успешна! Войдите.', 'success')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('❌ Пользователь уже существует!', 'error')
        conn.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('👋 До новых боёв!', 'success')
    return redirect('/')

# ===== ЧАТ =====
@app.route('/api/chat/messages', methods=['GET'])
def chat_messages():
    conn = sqlite3.connect('tanks.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT username, message, timestamp FROM messages ORDER BY id DESC LIMIT 50")
    messages = [{'username': row[0], 'message': row[1], 'time': row[2]} for row in c.fetchall()]
    conn.close()
    return jsonify({'messages': messages[::-1]})

@app.route('/api/chat/send', methods=['POST'])
def chat_send():
    username = session.get('username', 'Гость')
    message = request.json.get('message', '').strip()[:100]
    
    if message:
        score = 0
        conn = sqlite3.connect('tanks.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT score FROM leaderboard WHERE username=?", (username,))
        result = c.fetchone()
        if result: score = result[0]
        
        rank = get_rank(score)
        display_name = f"{rank} {username}"
        
        c.execute("INSERT INTO messages (username, message, timestamp) VALUES (?, ?, ?)",
                 (display_name, message, datetime.now().strftime('%H:%M')))
        update_score(username, 5)
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'error'})

# ===== ЗАМЕТКИ =====
@app.route('/api/notes', methods=['GET', 'POST'])
def notes():
    username = session.get('username', 'Гость')
    
    if request.method == 'POST':
        title = request.json.get('title', 'Заметка')[:50]
        content = request.json.get('content', '')[:500]
        if content:
            conn = sqlite3.connect('tanks.db', check_same_thread=False)
            c = conn.cursor()
            c.execute("INSERT INTO notes (title, content, timestamp, username) VALUES (?, ?, ?, ?)",
                     (title, content, datetime.now().strftime('%H:%M'), username))
            update_score(username, 10)
            conn.commit()
            conn.close()
            return jsonify({'status': 'ok'})
    
    conn = sqlite3.connect('tanks.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT title, content, timestamp FROM notes WHERE username=? OR username='' ORDER BY id DESC LIMIT 10", (username,))
    notes_list = [{'title': row[0], 'content': row[1], 'time': row[2]} for row in c.fetchall()]
    conn.close()
    return jsonify({'notes': notes_list})

# ===== БОИ =====
@app.route('/api/battle/<mode>', methods=['POST'])
def battle(mode):
    username = session.get('username', 'Гость')
    tank = request.json.get('tank', 'Т-34')
    
    if mode == 'pvp':
        win_chance = random.random()
        if win_chance > 0.6:
            reward = random.randint(200, 500)
            result = f"🏆 ПОБЕДА PVP! +{reward}"
        elif win_chance > 0.3:
            reward = 100
            result = f"🤝 НИЧЬЯ PVP! +{reward}"
        else:
            reward = 50
            result = f"⚔️ ПОРАЖЕНИЕ PVP! +{reward}"
    else:  # pve
        bot_tank = random.choice(['ИС-7', 'Tiger II', 'Maus', 'T29'])
        reward = random.randint(100, 300)
        result = f"🎯 {tank} vs {bot_tank}! +{reward}"
    
    update_score(username, reward)
    return jsonify({'result': result, 'reward': reward, 'tank': tank})

# ===== ГАРАЖ И КАТАЛОГ =====
@app.route('/api/garage')
def garage():
    username = session.get('username', 'Гость')
    conn = sqlite3.connect('tanks.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT DISTINCT tank_name FROM garage WHERE username=?", (username,))
    tanks = [row[0] for row in c.fetchall()]
    conn.close()
    return jsonify({'tanks': tanks or ['Т-34']})

@app.route('/api/buy_tank', methods=['POST'])
def buy_tank():
    username = session.get('username', 'Гость')
    tank = request.json.get('tank')
    if tank:
        conn = sqlite3.connect('tanks.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO garage (username, tank_name, bought_at) VALUES (?, ?, ?)",
                 (username, tank, datetime.now().strftime('%Y-%m-%d %H:%M')))
        conn.commit()
        conn.close()
        return jsonify({'status': '✅ Танк куплен!'})
    return jsonify({'status': '❌ Ошибка'})

@app.route('/api/tanks')
def tanks():
    return jsonify({
        "СССР": {"3": ["Т-34", "КВ-1"], "5": ["ИС-3"], "7": ["ИС-7"], "10": ["Obj.277"]},
        "Германия": {"5": ["Tiger I"], "7": ["Tiger II"], "8": ["Maus"], "10": ["E-100"]},
        "США": {"5": ["T29"], "8": ["M103"], "10": ["T110E5"]}
    })

@app.route('/api/stats')
def stats():
    username = session.get('username', 'Гость')
    conn = sqlite3.connect('tanks.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT score FROM leaderboard WHERE username=?", (username,))
    score_result = c.fetchone()
    score = score_result[0] if score_result else 0
    rank = get_rank(score)
    conn.close()
    return jsonify({'username': username, 'score': score, 'rank': rank})

if __name__ == '__main__':
    app.run(debug=True)
