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

def join_game(id):
    pass

def create_new_game():
    print("creating new game!")
    cursor.execute(f"INSERT INTO games (chessboard_state, searching) VALUES ('1Q6/5pk1/2p3p1/1p2N2p/1b5P/1bn5/2r3P1/2K5 w - - 16 42', 1)")
    db.commit()
    primary_key = cursor.lastrowid
    emit("request_game_response", {"chessboard_state":'r6k/p4pb1/2NBr2p/5N2/2PP1pn1/1Q2p3/P3P1Bq/R2R1K2 w - - 3 28', "id":primary_key})

@app.route('/')
def index():
    return render_template('game.html')

@socketio.on('request_game')
def handle_request_game():
    cursor.execute("SELECT id FROM games where id IS TRUE")
    results = cursor.fetchall()
    if results:
        join_game(results[0][0])
    else:
        create_new_game()

@socketio.on("join")
def on_join(data):
    username = "someone"
    room = data["room"]
    join_room(room)
    send(username + "has joined the game!", to=room)

@socketio.on("leave")
def on_leave(data):
    username = "someone"
    room = data["room"]
    leave_room(room)
    send(username + "has left the game!", to=room)

# @socketio.on('move')
# def handle_move(data):
#     game = DB_Game.query.get(data['game_id'])
#     move = chess.Move.from_uci(data['move'])
#     if move in game.board.legal_moves:
#         game.board.push(move)
#         db.session.commit() # save the game state
#         return game.board.fen() # return the new board state
#     else:
#         return 'invalid', 400

if __name__ == '__main__':
    socketio.run(app, debug=True)