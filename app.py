from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
import json
import os
from datetime import datetime
from functools import wraps
import hashlib

app = Flask(__name__)
app.secret_key = 'tank-battalion-2026-super-secret-key-change-in-production'

def get_tankist_rank(score):
    """Полная система 32 званий по очкам"""
    ranks = [
        (0, "Новобранец"),
        (100, "Рядовой"),
        (500, "Ефрейтор"),
        (1_000, "Капрал"),
        (2_500, "Мастер-капрал"),
        (5_000, "Сержант"),
        (10_000, "Штаб-сержант"),
        (25_000, "Мастер-сержант"),
        (50_000, "Первый сержант"),
        (100_000, "Сержант-майор"),
        (250_000, "Уорэнт-офицер 1"),
        (500_000, "Уорэнт-офицер 2"),
        (750_000, "Уорэнт-офицер 3"),
        (1_000_000, "Уорэнт-офицер 4"),
        (1_500_000, "Уорэнт-офицер 5"),
        (2_000_000, "Младший лейтенант"),
        (3_000_000, "Лейтенант"),
        (5_000_000, "Старший лейтенант"),
        (7_500_000, "Капитан"),
        (10_000_000, "Майор"),
        (15_000_000, "Подполковник"),
        (20_000_000, "Полковник"),
        (25_000_000, "Бригадир"),
        (30_000_000, "Генерал-майор"),
        (40_000_000, "Генерал-лейтенант"),
        (50_000_000, "Генерал"),
        (75_000_000, "Маршал"),
        (100_000_000, "Фельдмаршал"),
        (150_000_000, "Командор ⭐"),
        (250_000_000, "Генералиссимус ⭐⭐"),
        (500_000_000, "Легенда ⭐⭐⭐"),
        (999_999_999, "Ветеран Tank Battalion 🔥🔥🔥")
    ]
    
    for threshold, rank in reversed(ranks):
        if score >= threshold:
            return rank
    return "Новобранец"

def get_rank_icon(rank):
    if "Ветеран" in rank: return "🔥🔥🔥 "
    if "Легенда" in rank: return "⭐⭐⭐ "
    if "Генералиссимус" in rank: return "⭐⭐ "
    if "Командор" in rank: return "⭐ "
    if "Фельдмаршал" in rank: return "⚔️ "
    if "Маршал" in rank: return "👑 "
    if "Генерал" in rank: return "🎖️ "
    return ""

def update_user_score(username, points):
    """Добавляет очки игроку"""
    conn = sqlite3.connect('tanks.db')
    c = conn.cursor()
    
    # Обновляем или создаём запись
    c.execute("""
        INSERT INTO leaderboard (username, score, updated_at) 
        VALUES (?, COALESCE((SELECT score FROM leaderboard WHERE username=?), 0) + ?, ?)
        ON CONFLICT(username) DO UPDATE SET 
        score = score + excluded.score, 
        updated_at = excluded.updated_at
    """, (username, username, points, datetime.now().strftime('%Y-%m-%d %H:%M')))
    
    conn.commit()
    conn.close()

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
        
        # Получаем очки
        conn = sqlite3.connect('tanks.db')
        c = conn.cursor()
        c.execute("SELECT score FROM leaderboard WHERE username=? ORDER BY updated_at DESC LIMIT 1", (username,))
        score_result = c.fetchone()
        user_score = score_result[0] if score_result else 0
        conn.close()
        
        rank = get_tankist_rank(user_score)
        icon = get_rank_icon(rank)
        display_name = f"{icon}[{rank}] {username}"
        
        message = request.form.get('message', '').strip()[:200]
        timestamp = datetime.now().strftime('%H:%M')
        
        if message:
            conn = sqlite3.connect('tanks.db')
            c = conn.cursor()
            c.execute("INSERT INTO messages (username, message, timestamp) VALUES (?, ?, ?)",
                      (display_name, message, timestamp))
            # +5 очков за сообщение!
            update_user_score(username, 5)
            conn.commit()
            conn.close()
            return jsonify({'status': 'ok'})
    
    # Загрузка сообщений
    conn = sqlite3.connect('tanks.db')
    c = conn.cursor()
    c.execute("SELECT username, message, timestamp FROM messages ORDER BY id DESC LIMIT 50")
    messages = c.fetchall()
    conn.close()
    return jsonify({'messages': messages[::-1]})

    # GET - загрузка сообщений
    conn = sqlite3.connect('tanks.db')
    c = conn.cursor()
    c.execute("SELECT username, message, timestamp FROM messages ORDER BY id DESC LIMIT 50")
    messages = c.fetchall()
    conn.close()
    
    return jsonify({'messages': messages[::-1]})  # Новые сверху

@app.route('/battle', methods=['POST'])
def battle():
    data = request.json
    username = session.get('username', 'Танкист')
    player_tank = data.get('tank', 'Т-34')
    bot_tank = get_random_bot_tank()
    
    # Симуляция боя (реальные танки WoT)
    player_hp = 1200
    bot_hp = 1400
    player_damage = random.randint(300, 450)
    bot_damage = random.randint(250, 400)
    
    # 5 раундов боя
    for round in range(5):
        # Удар игрока
        bot_hp -= player_damage
        if bot_hp <= 0:
            reward = 250  # Победа!
            result = f"✅ ПОБЕДА! {player_tank} уничтожил {bot_tank}!"
            break
        
        # Удар бота
        player_hp -= bot_damage
        if player_hp <= 0:
            reward = 50  # Поражение
            result = f"❌ ПОРАЖЕНИЕ! {bot_tank} уничтожил {player_tank}"
            break
    else:
        reward = 100  # Ничья
        result = "🤝 Ничья! Оба танка выведены из строя"
    
    update_user_score(username, reward)
    return jsonify({
        'result': result,
        'reward': reward,
        'player_tank': player_tank,
        'bot_tank': bot_tank
    })

@app.route('/garage')
def garage():
    username = session.get('username', 'Танкист')
    conn = sqlite3.connect('tanks.db')
    c = conn.cursor()
    c.execute("SELECT tank_name FROM garage WHERE username=?", (username,))
    tanks = [row[0] for row in c.fetchall()]
    conn.close()
    return jsonify({'tanks': tanks or ['Т-34']})  # Базовый танк

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

