from flask import Flask, request, render_template, url_for, flash, redirect, session
from flask_login import login_user, logout_user, login_required, current_user, UserMixin, LoginManager
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import os, json

DEV = False

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", default="krudsoppa")
db = mysql.connector.connect(
    host=os.getenv("MYSQLHOST", default="localhost"),
    port=os.getenv("MYSQLPORT", default=3306),
    user=os.getenv("MYSQLUSER", default="root"),
    password=os.getenv("MYSQLPASSWORD", default="")
)
login = LoginManager(app)
login.init_app(app)
socketio = SocketIO(app)
cursor = db.cursor()
users_searching = []
db_name = "online_chess"
DIR_PATH = os.path.abspath(os.path.dirname(__file__))

# Predefined tables
with open(os.path.join(DIR_PATH, "database.json")) as f:
    db_tables = json.load(f)

# Help from Kalle
cursor.execute("SHOW DATABASES")

# Creates database if it does not exist
if db_name not in [x[0] for x in cursor.fetchall()]:
    cursor.execute(f"CREATE DATABASE {db_name}")
db.connect(database=db_name) # Connects to database

# Ensures all neccessary tables exists 
cursor.execute("SHOW TABLES")
existing_tables = [x[0] for x in cursor.fetchall()]
for table_name in db_tables.keys():
    if table_name not in existing_tables:
        # If table in database does not exist
        required_columns = db_tables[table_name]
        sql_commands = []
        for name, cmd in required_columns.items():
            # Format column name into sql command
            sql_commands.append(cmd % name)
        cursor.execute(f"CREATE TABLE {table_name} ({', '.join(sql_commands)})")
        #ex CREATE TABLE post (id bigint(20) NOT NULL PRIMARY KEY AUTO_INCREMENT, name varchar(100) ... )

cursor.close()
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
    # return render_template("test.html")

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

@app.route("/play")
@login_required
def play():
    user = current_user
    return render_template("play.html", user=user)

@app.route("/users")
@login_required
def users():
    cursor.execute("SELECT id, username, email FROM users")
    results = cursor.fetchall()
    user = current_user
    return render_template("users.html", users=results, user=user)

@app.route("/games")
@login_required
def games():
    user = current_user
    cursor.execute("SELECT id, white_pieces_userid, black_pieces_userid, game_info FROM games WHERE game_finished=1" )
    results = cursor.fetchall()
    adjusted_results = []
    for result in results:
        adjusted_results.append({"id":result["id"], "white_username":get_user_by_id(result["white_pieces_userid"])["username"],
                                 "black_username":get_user_by_id(result["black_pieces_userid"])["username"], "winner":result["game_info"].split(",")[0]} )
    return render_template("games.html", games=adjusted_results, user=user)

@app.route("/profile")
@login_required
def profile():
    user = current_user
    user_id = user.id
    cursor.execute(f"SELECT id, white_pieces_userid, black_pieces_userid, game_info FROM games WHERE game_finished=1 AND (white_pieces_userid = '{user_id}' OR black_pieces_userid = '{user_id}')" )
    results = cursor.fetchall()
    adjusted_results = []
    for result in results:
        adjusted_results.append({"id":result["id"], "white_username":get_user_by_id(result["white_pieces_userid"])["username"],
                                 "black_username":get_user_by_id(result["black_pieces_userid"])["username"], "winner":result["game_info"].split(",")[0]} )
    return render_template("profile.html", games=adjusted_results, user=user)


class User(UserMixin):
    def __init__(self, user_info):
        self.id = user_info["id"]
        self.username = user_info["username"]
        self.email = user_info["email"]
        self.password_hash = user_info["password_hash"]

class DB_Game:
    def __init__(self, id=None, white_pieces_userid=None, black_pieces_userid=None, chessboard_state="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", game_finished=0, game_info=None) -> None:
        self.id = id
        self.white_pieces_userid = white_pieces_userid
        self.black_pieces_userid = black_pieces_userid
        self.chessboard_state = chessboard_state
        self.game_finished = game_finished
        self.game_info = game_info

def get_user_by_username(username):
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()
    print(user)
    return user

def get_user_by_id(id):
    cursor.execute("SELECT * FROM users WHERE id=%s", (id,))
    user = cursor.fetchone()
    return user

def create_user(username, email, password):
    password_hash = generate_password_hash(password)
    cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", (username, email, password_hash,))
    db.commit()

def check_password(username, password):
    user = get_user_by_username(username)
    if user is None:
        print("False user")
        return False
    print(user)
    return check_password_hash(user['password_hash'], password)

def create_new_game(player1, player2):
    print("Creating new game!")
    users_searching.remove(player1)
    db_game = DB_Game(white_pieces_userid=player1[0], black_pieces_userid=player2[0])
    cursor.execute(f"INSERT INTO games (white_pieces_userid,  black_pieces_userid, chessboard_state) VALUES ('{db_game.white_pieces_userid}','{db_game.black_pieces_userid}','{db_game.chessboard_state}')")
    db.commit()
    db_game.id = cursor.lastrowid
    cursor.execute(f"SELECT * FROM games WHERE id = {db_game.id}")
    database_game = cursor.fetchone()
    join_room(f"{db_game.id}", player1[1])
    join_room(f"{db_game.id}", player2[1])
    emit("request_game_response", database_game, room=f"{db_game.id}")

@socketio.on('request_game')
def handle_request_game():
    if not users_searching:
        return users_searching.append([current_user.id, request.sid])
    elif (users_searching[0][0] == current_user.id):
        return
    return create_new_game(users_searching[0], [current_user.id, request.sid])

@socketio.on("request_user")
def handle_request_userid():
    print(current_user.id, current_user.username)
    emit("request_user_response", {"username": current_user.username, "id": current_user.id})

@socketio.on("request_opponent_username")
def handle_request_opponent_username(data):
    user = get_user_by_id(data)
    emit("request_opponent_username_response", user["username"])

@socketio.on("send-chat-message")
def handle_send_chat_message(data):
    emit("chat-message", data["input"], room=data["room"])

@socketio.on("finished-game")
def handle_finished_game(data):
    pgn = data["pgn"]
    game_id = data["id"]
    game_result = data["result"]
    game_info = f"{game_result},{pgn}"

    cursor.execute(f"SELECT * FROM games WHERE id={game_id}")
    game = cursor.fetchone()
    if game["game_finished"] == 1:
        return
    else:
        cursor.execute(f"UPDATE games SET game_finished=1, game_info='{game_info}' WHERE id='{game_id}'")
        db.commit()

@socketio.on('move')
def handle_move(data):
  fen = data["fen"]
  id = data["room"]
  cursor.execute(f"UPDATE games SET chessboard_state = '{fen}' WHERE id='{id}'")
  db.commit()
  emit("move", data, room=id)

host = "localhost" if DEV else "0.0.0.0"

if __name__ == '__main__':
    socketio.run(app, debug=DEV, host=host, port=os.getenv("PORT", default=5000), allow_unsafe_werkzeug=True)