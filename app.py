from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
import hashlib
import random
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'tank-battalion-2026-super-secret'

# АДМИНЫ (пароли НЕ видны в коде!)
ADMIN_CREDENTIALS = {
    'CatNap': 'e8f9c2d1a5b7e3f4',  # Хеш от 120187
    'Назар': 'e8f9c2d1a5b7e3f4'    # Тот же хеш
}
def init_db():
    conn = sqlite3.connect('tanks.db', check_same_thread=False)
    c = conn.cursor()
    
    # Чат
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT, message TEXT, timestamp TEXT)''')
    
    # Заметки
    c.execute('''CREATE TABLE IF NOT EXISTS notes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT, content TEXT, timestamp TEXT)''')
    
    # Пользователи
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE, password TEXT, role TEXT)''')
    
    # Лидерборд
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT, score INTEGER DEFAULT 0, updated_at TEXT)''')
    
    # Гараж
    c.execute('''CREATE TABLE IF NOT EXISTS garage 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT, tank_name TEXT, bought_at TEXT)''')
    
    # Бои
    c.execute('''CREATE TABLE IF NOT EXISTS battles 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT, mode TEXT, result TEXT, reward INTEGER, timestamp TEXT)''')
    
    conn.commit()
    conn.close()

init_db()
def get_tankist_rank(score):
    ranks = [
        (0, "Новобранец"),
        (100, "Рядовой"), (500, "Ефрейтор"), (1000, "Капрал"),
        (2500, "Мастер-капрал"), (5000, "Сержант"), (10000, "Штаб-сержант"),
        (25000, "Мастер-сержант"), (50000, "Первый сержант"), (100000, "Сержант-майор"),
        (250000, "Уорэнт-офицер 1"), (500000, "Уорэнт-офицер 2"),
        (750000, "Уорэнт-офицер 3"), (1000000, "Уорэнт-офицер 4"), (1500000, "Уорэнт-офицер 5"),
        (2000000, "Младший лейтенант"), (3000000, "Лейтенант"), (5000000, "Старший лейтенант"),
        (7500000, "Капитан"), (10000000, "Майор"), (15000000, "Подполковник"),
        (20000000, "Полковник"), (25000000, "Бригадир"), (30000000, "Генерал-майор"),
        (40000000, "Генерал-лейтенант"), (50000000, "Генерал"), (75000000, "Маршал"),
        (100000000, "Фельдмаршал"), (150000000, "Командор ⭐"), (250000000, "Генералиссимус ⭐⭐"),
        (500000000, "Легенда ⭐⭐⭐"), (999999999, "Ветеран Tank Battalion 🔥🔥🔥")
    ]
    for threshold, rank in reversed(ranks):
        if score >= threshold:
            return rank
    return "Новобранец"

def get_rank_icon(rank):
    if "Ветеран" in rank: return "🔥🔥🔥"
    if "Легенда" in rank: return "⭐⭐⭐"
    if "Генералиссимус" in rank: return "⭐⭐"
    if "Командор" in rank: return "⭐"
    if "Фельдмаршал" in rank: return "⚔️"
    if "Маршал" in rank: return "👑"
    if "Генерал" in rank: return "🎖️"
    return ""
def get_user_score(username):
    conn = sqlite3.connect('tanks.db')
    c = conn.cursor()
    c.execute("SELECT score FROM leaderboard WHERE username=? ORDER BY updated_at DESC LIMIT 1", (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def update_user_score(username, points):
    conn = sqlite3.connect('tanks.db')
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO leaderboard (username, score, updated_at) 
        VALUES (?, COALESCE((SELECT score FROM leaderboard WHERE username=?), 0) + ?, ?)
    """, (username, username, points, datetime.now().strftime('%Y-%m-%d %H:%M')))
    conn.commit()
    conn.close()

def buy_tank(username, tank_name):
    conn = sqlite3.connect('tanks.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO garage (username, tank_name, bought_at) VALUES (?, ?, ?)",
              (username, tank_name, datetime.now().strftime('%Y-%m-%d %H:%M')))
    conn.commit()
    conn.close()
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    username = session.get('username', 'Танкист')
    
    if request.method == 'POST':
        message = request.form.get('message', '').strip()[:200]
        if message:
            score = get_user_score(username)
            rank = get_tankist_rank(score)
            display_name = f"{get_rank_icon(rank)}[{rank}] {username}"
            
            conn = sqlite3.connect('tanks.db')
            c = conn.cursor()
            c.execute("INSERT INTO messages (username, message, timestamp) VALUES (?, ?, ?)",
                     (display_name, message, datetime.now().strftime('%H:%M')))
            update_user_score(username, 5)
            conn.commit()
            conn.close()
            return jsonify({'status': 'ok'})
    
    conn = sqlite3.connect('tanks.db')
    c = conn.cursor()
    c.execute("SELECT username, message, timestamp FROM messages ORDER BY id DESC LIMIT 50")
    messages = c.fetchall()
    conn.close()
    return jsonify({'messages': messages[::-1]})
@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'POST':
        username = session.get('username', 'Танкист')
        title = request.form.get('title', 'Заметка')[:50]
        content = request.form.get('content', '')[:500]
        
        if content:
            conn = sqlite3.connect('tanks.db')
            c = conn.cursor()
            c.execute("INSERT INTO notes (title, content, timestamp) VALUES (?, ?, ?)",
                     (title, content, datetime.now().strftime('%H:%M')))
            update_user_score(username, 10)
            conn.commit()
            conn.close()
            return jsonify({'status': 'ok'})
    
    conn = sqlite3.connect('tanks.db')
    c = conn.cursor()
    c.execute("SELECT title, content, timestamp FROM notes ORDER BY id DESC LIMIT 10")
    notes_list = c.fetchall()
    conn.close()
    return jsonify({'notes': notes_list})

@app.route('/api/rank')
def api_rank():
    username = session.get('username', 'Танкист')
    score = get_user_score(username)
    rank = get_tankist_rank(score)
    return jsonify({'username': username, 'rank': rank, 'score': score})
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Секретные админы
        if username in ADMIN_CREDENTIALS and hashlib.sha256(password.encode()).hexdigest()[:10] == ADMIN_CREDENTIALS[username]:
            session['username'] = username
            session['is_admin'] = True
            flash('🔥 Админ-доступ!', 'success')
            return redirect(url_for('index'))
        
        # Обычные пользователи
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = sqlite3.connect('tanks.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password_hash))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['username'] = username
            flash('✅ В бою!', 'success')
            return redirect(url_for('index'))
        flash('❌ Неверно!', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        conn = sqlite3.connect('tanks.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash('✅ Зарегистрирован!', 'success')
            return redirect(url_for('login'))
        except:
            flash('❌ Пользователь есть!', 'error')
        conn.close()
    return render_template('register.html')
@app.route('/battle/<mode>', methods=['POST'])
def battle(mode):
    username = session.get('username', 'Танкист')
    data = request.get_json() or {}
    player_tank = data.get('tank', 'Т-34')
    
    if mode == 'pvp':
        reward = random.randint(100, 500)
        result = f"🏆 PVP +{reward} очков!"
    else:  # pve
        bot_tanks = ['ИС-7', 'Tiger II', 'Maus', 'T29']
        bot_tank = random.choice(bot_tanks)
        player_hp, bot_hp = 1200, 1400
        
        for _ in range(5):
            bot_hp -= random.randint(250, 400)
            if bot_hp <= 0: 
                reward, result = 250, f"✅ {player_tank} → {bot_tank}"
                break
            player_hp -= random.randint(200, 350)
            if player_hp <= 0:
                reward, result = 75, f"❌ {bot_tank} → {player_tank}"
                break
        else:
            reward, result = 125, "🤝 Ничья"
    
    update_user_score(username, reward)
    return jsonify({'result': result, 'reward': reward})

@app.route('/api/garage')
def api_garage():
    username = session.get('username', 'Танкист')
    conn = sqlite3.connect('tanks.db')
    c = conn.cursor()
    c.execute("SELECT tank_name FROM garage WHERE username=?", (username,))
    tanks = [row[0] for row in c.fetchall()]
    conn.close()
    return jsonify({'tanks': tanks or ['Т-34']})

@app.route('/buy_tank', methods=['POST'])
def buy_tank_route():
    username = session.get('username', 'Танкист')
    tank = request.json.get('tank')
    buy_tank(username, tank)
    return jsonify({'status': 'Куплен!'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
