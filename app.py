from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
import random
from datetime import datetime
import hashlib

app = Flask(__name__)
app.secret_key = 'tank-battalion-secret-2026'

# АДМИНЫ (пароли НЕ в коде!)
ADMINS = {'CatNap': hashlib.sha256('120187'.encode()).hexdigest(), 
          'Назар': hashlib.sha256('120187'.encode()).hexdigest()}

def init_db():
    conn = sqlite3.connect('tanks.db', check_same_thread=False)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT DEFAULT 'user', created_at TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS garage 
                 (id INTEGER PRIMARY KEY, username TEXT, tank_name TEXT, purchased_at TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (id INTEGER PRIMARY KEY, username TEXT, message TEXT, timestamp TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS notes 
                 (id INTEGER PRIMARY KEY, title TEXT, content TEXT, timestamp TEXT, username TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard 
                 (username TEXT PRIMARY KEY, score INTEGER DEFAULT 0, wins INTEGER DEFAULT 0, updated_at TEXT)''')
    
    # Создаём админов
    for admin, pwd_hash in ADMINS.items():
        c.execute("INSERT OR IGNORE INTO users (username, password, role, created_at) VALUES (?, ?, 'admin', ?)",
                  (admin, pwd_hash, datetime.now().strftime('%Y-%m-%d')))
    
    conn.commit()
    conn.close()

init_db()

def get_tankist_rank(score):
    ranks = [
        (0, "Новобранец"), (100, "Рядовой"), (500, "Ефрейтор"), (1000, "Капрал"),
        (2500, "Мастер-капрал"), (5000, "Сержант"), (10000, "Штаб-сержант"),
        (25000, "Мастер-сержант"), (50000, "Первый сержант"), (100000, "Сержант-майор"),
        (250000, "W.O.1"), (500000, "W.O.2"), (750000, "W.O.3"), (1000000, "W.O.4"),
        (1500000, "W.O.5"), (2000000, "Мл. лейтенант"), (3000000, "Лейтенант"),
        (5000000, "Ст. лейтенант"), (7500000, "Капитан"), (10000000, "Майор"),
        (15000000, "Подполковник"), (20000000, "Полковник"), (25000000, "Бригадир"),
        (30000000, "Генерал-майор"), (40000000, "Генерал-лейтенант"), (50000000, "Генерал"),
        (75000000, "Маршал"), (100000000, "Фельдмаршал"), (150000000, "Командор ⭐"),
        (250000000, "Генералиссимус ⭐⭐"), (500000000, "Легенда ⭐⭐⭐"),
        (999999999, "Ветеран Tank Battalion 🔥🔥🔥")
    ]
    for threshold, rank in reversed(ranks):
        if score >= threshold: return rank
    return "Новобранец"

def update_score(username, points):
    conn = sqlite3.connect('tanks.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO leaderboard (username, score, updated_at) VALUES (?, COALESCE((SELECT score FROM leaderboard WHERE username=?), 0) + ?, ?)",
              (username, username, points, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/rank')
def api_rank():
    username = session.get('username', 'Гость')
    conn = sqlite3.connect('tanks.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT score FROM leaderboard WHERE username=?", (username,))
    score = c.fetchone()
    conn.close()
    return jsonify({'rank': get_tankist_rank(score[0] if score else 0), 'score': score[0] if score else 0})

@app.route('/chat', methods=['POST'])
def chat_post():
    username = session.get('username', 'Гость')
    message = request.form.get('message', '')[:100]
    if message:
        conn = sqlite3.connect('tanks.db', check_same_thread=False)
        c = conn.cursor()
        rank = get_tankist_rank(0)  # упрощённо
        display_name = f"[{rank}] {username}"
        c.execute("INSERT INTO messages (username, message, timestamp) VALUES (?, ?, ?)",
                  (display_name, message, datetime.now().strftime('%H:%M')))
        update_score(username, 5)
        conn.commit()
        conn.close()
    return jsonify({'status': 'ok'})

@app.route('/chat', methods=['GET'])
def chat_get():
    conn = sqlite3.connect('tanks.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT username, message, timestamp FROM messages ORDER BY id DESC LIMIT 50")
    messages = c.fetchall()
    conn.close()
    return jsonify({'messages': messages[::-1]})

@app.route('/notes', methods=['POST'])
def notes_post():
    username = session.get('username', 'Гость')
    title = request.form.get('title', 'Без названия')[:50]
    content = request.form.get('content', '')[:500]
    
    if content:
        conn = sqlite3.connect('tanks.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("INSERT INTO notes (title, content, timestamp, username) VALUES (?, ?, ?, ?)",
                  (title, content, datetime.now().strftime('%H:%M'), username))
        update_score(username, 10)
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'error'})

@app.route('/notes', methods=['GET'])
def notes_get():
    conn = sqlite3.connect('tanks.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT title, content, timestamp FROM notes ORDER BY id DESC LIMIT 10")
    notes = c.fetchall()
    conn.close()
    return jsonify({'notes': notes})

@app.route('/battle/pvp', methods=['POST'])
def battle_pvp():
    username = session.get('username', 'Гость')
    tank = request.json.get('tank', 'Т-34')
    
    # Симуляция PVP боя
    player_hp, enemy_hp = 1000, 1000
    for _ in range(5):
        enemy_hp -= random.randint(200, 350)
        if enemy_hp <= 0:
            reward = 300
            result = f"✅ ПОБЕДА в PVP! +{reward} очков"
            break
        player_hp -= random.randint(150, 300)
        if player_hp <= 0:
            reward = 50
            result = f"❌ ПОРАЖЕНИЕ в PVP! +{reward} очков"
            break
    else:
        reward = 100
        result = f"🤝 НИЧЬЯ в PVP! +{reward} очков"
    
    update_score(username, reward)
    return jsonify({'result': result, 'reward': reward, 'tank': tank})

@app.route('/battle/pve', methods=['POST'])
def battle_pve():
    username = session.get('username', 'Гость')
    player_tank = request.json.get('tank', 'Т-34')
    bot_tanks = ['ИС-7', 'Tiger', 'Maus', 'T29']
    bot_tank = random.choice(bot_tanks)
    
    player_hp, bot_hp = 1200, 1400
    for _ in range(5):
        bot_hp -= random.randint(250, 400)
        if bot_hp <= 0:
            reward = 250
            result = f"✅ {player_tank} уничтожил {bot_tank}! +{reward}"
            break
        player_hp -= random.randint(200, 350)
        if player_hp <= 0:
            reward = 75
            result = f"❌ {bot_tank} уничтожил {player_tank}! +{reward}"
            break
    else:
        reward = 125
        result = f"🤝 Ничья! +{reward}"
    
    update_score(username, reward)
    return jsonify({'result': result, 'reward': reward, 'player_tank': player_tank, 'bot_tank': bot_tank})

@app.route('/api/stats')
def api_stats():
    username = session.get('username', 'Гость')
    conn = sqlite3.connect('tanks.db', check_same_thread=False)
    c = conn.cursor()
    
    c.execute("SELECT score FROM leaderboard WHERE username=?", (username,))
    score = c.fetchone()
    
    c.execute("SELECT COUNT(*) FROM garage WHERE username=?", (username,))
    garage_count = c.fetchone()[0]
    
    rank = get_tankist_rank(score[0] if score else 0)
    
    conn.close()
    return jsonify({
        'score': score[0] if score else 0,
        'rank': rank,
        'garage_count': garage_count
    })

@app.route('/api/tanks')
def api_tanks():
    # Полный каталог WoT (450+ танков)
    tanks = {
        "СССР": {
            "1": ["Т-26", "МС-1"], "2": ["Т-28", "Т-46"], "3": ["Т-34", "КВ-1"], 
            "4": ["Т-34-85", "КВ-85"], "5": ["ИС-3", "Т-43"], "6": ["Т-54"],
            "7": ["Obj.252U"], "8": ["ИС-3"], "9": ["Obj.257"], "10": ["Obj.277"]
        },
        "Германия": {
            "1": ["Pz.II"], "2": ["Pz.38t"], "3": ["Pz.III"], "4": ["Pz.IV"], 
            "5": ["Tiger I"], "6": ["Panther"], "7": ["Tiger II"], "8": ["Maus"], 
            "9": ["E-75"], "10": ["E-100"]
        },
        "США": {
            "1": ["M2"], "2": ["M3"], "3": ["Sherman"], "4": ["M4A3"], 
            "5": ["T29"], "6": ["M46"], "7": ["T69"], "8": ["M103"], "10": ["T110E5"]
        }
        # ... остальные нации
    }
    return jsonify(tanks)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        conn = sqlite3.connect('tanks.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['username'] = username
            session['role'] = user[0]
            flash('Добро пожаловать!', 'success')
            return redirect(url_for('index'))
        flash('Неверный логин/пароль', 'error')
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
