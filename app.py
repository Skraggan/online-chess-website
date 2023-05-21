from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room, send
import mysql.connector
import chess

app = Flask(__name__)
db = mysql.connector.connect(
    host="localhost",
    user="root",
    database="online_chess"
)
socketio = SocketIO(app)

cursor = db.cursor()

class DB_Game:
    def __init__(self, id=None, chessboard_state="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", searching=1, paricipants=None) -> None:
        self.id = id
        self.chessboard_state = chessboard_state
        self.searching = searching
        self.participants = paricipants

def join_game(id):
    print("Joining an existing game!")
    cursor.execute(f"UPDATE games SET searching = 0 WHERE id = {id}")
    db.commit()
    cursor.execute(f"SELECT * FROM games WHERE id = {id}")
    database_game = cursor.fetchall()[0]
    database_game = list(database_game)
    emit("request_game_response", database_game)

def create_new_game():
    print("Creating new game!")
    db_game = DB_Game()
    cursor.execute(f"INSERT INTO games (chessboard_state, searching) VALUES ('{db_game.chessboard_state}', '{db_game.searching}')")
    db.commit()
    db_game.id = cursor.lastrowid
    database_game = [db_game.id, db_game.chessboard_state, db_game.searching, db_game.participants]
    emit("request_game_response", database_game)

@app.route('/')
def index():
    return render_template('game.html')

@socketio.on('request_game')
def handle_request_game():
    cursor.execute("SELECT id FROM games where searching IS TRUE")
    results = cursor.fetchall()
    if results:
        join_game(results[-1][0])
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