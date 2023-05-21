from flask import Flask, request, render_template, url_for, flash, redirect, session
from flask_login import login_user, logout_user, login_required, current_user, UserMixin, LoginManager
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import chess

app = Flask(__name__)
app.config['SECRET_KEY'] = 'krudsoppa'
db = mysql.connector.connect(
    host="localhost",
    user="root",
    database="online_chess"
)
login = LoginManager(app)
login.init_app(app)
socketio = SocketIO(app)
cursor = db.cursor(dictionary=True)

@login.user_loader
def load_user(user_id):
    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user_info = cursor.fetchone()
    if user_info:
        return User(user_info)
    return None

@app.route('/')
def index():
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    else:
        return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        user = get_user_by_username(username)
        if user is not None:
            flash('User already exists')
            return redirect(url_for('register'))
        create_user(username, email, password)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not check_password(username, password):
            flash('Invalid login')
            return redirect(url_for('login'))
        user = get_user_by_username(username)
        login_user(User(user))
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/home')
@login_required
def home():
    user = current_user
    return render_template("home.html", user=user)

@app.route("/game")
@login_required
def game():
    return render_template("game.html")

class User(UserMixin):
    def __init__(self, user_info):
        self.id = user_info["id"]
        self.username = user_info["username"]
        self.email = user_info["email"]
        self.password_hash = user_info["password_hash"]

class DB_Game:
    def __init__(self, id=None, chessboard_state="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", searching=1, paricipants=None) -> None:
        self.id = id
        self.chessboard_state = chessboard_state
        self.searching = searching
        self.participants = paricipants

def get_user_by_username(username):
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()
    return user

def create_user(username, email, password):
    password_hash = generate_password_hash(password)
    cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", (username, email, password_hash,))
    db.commit()

def check_password(username, password):
    user = get_user_by_username(username)
    if user is None:
        return False
    print(user)
    return check_password_hash(user['password_hash'], password)

def join_game(id):
    print("Joining an existing game!")
    cursor.execute(f"UPDATE games SET searching = 0 WHERE id = {id}")
    db.commit()
    cursor.execute(f"SELECT * FROM games WHERE id = {id}")
    database_game = cursor.fetchone()
    emit("request_game_response", database_game)

def create_new_game():
    print("Creating new game!")
    db_game = DB_Game()
    cursor.execute(f"INSERT INTO games (chessboard_state, searching) VALUES ('{db_game.chessboard_state}', '{db_game.searching}')")
    db.commit()
    db_game.id = cursor.lastrowid
    cursor.execute(f"SELECT * FROM games WHERE id = {db_game.id}")
    database_game = cursor.fetchone()
    emit("request_game_response", database_game)

@socketio.on('request_game')
def handle_request_game():
    cursor.execute("SELECT id FROM games where searching IS TRUE")
    result = cursor.fetchone()
    print(result)
    if result:
        join_game(result['id'])
    else:
        create_new_game()

@socketio.on("join")
def on_join(data):
    username = "Someone"
    room = data["room"]
    join_room(room)
    send(username + " has joined the game!", to=room)

@socketio.on("leave")
def on_leave(data):
    username = "Someone"
    room = data["room"]
    leave_room(room)
    send(username + " has left the game!", to=room)

@socketio.on('move')
def handle_move(data):
  emit("move", data, room=data["room"])

if __name__ == '__main__':
    socketio.run(app, debug=True)