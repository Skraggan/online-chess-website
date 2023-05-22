var board = null;
var game = new Chess("8/8/8/8/8/8/8/8 w - - 0 1");
var $status = $("#status");
var $fen = $("#fen");
var $pgn = $("#pgn");

var socket = io();

var messages = document.getElementById("messages");
var form = document.getElementById("form");
var input = document.getElementById("input");

var started = false;
var finished = false;
var team = null;
var room = null;
var user = null;
var chess_opponent_id = null;
var chess_opponent_username = null;
var config = {
  draggable: true,
  onDragStart: onDragStart,
  onDrop: onDrop,
  onSnapEnd: onSnapEnd,
};

board = Chessboard("board", config);
updateStatus();

function onDragStart(source, piece, position, orientation) {
  //   do not pick up pieces if the game is over
  if (game.game_over()) return false;

  // only pick up your own pieces if its your turn
  if (
    (orientation === "white" &&
      (game.turn() === "b" || piece.search(/^w/) === -1)) ||
    (orientation === "black" &&
      (game.turn() === "w" || piece.search(/^b/) === -1))
  ) {
    return false;
  }
}

function onDrop(source, target) {
  // see if the move is legal
  var move = game.move({
    from: source,
    to: target,
    promotion: "q",
  });

  // illegal move
  if (move === null) return "snapback";

  socket.emit("move", {
    from: source,
    to: target,
    room: room,
    fen: game.fen(),
  });
  console.log(`history: ${game.history()}`);

  updateStatus();
}

function onSnapEnd() {
  board.position(game.fen());
}

function finishedGame(result) {
  finished = true;
  winner = null;
  console.log("finished game");
  if (result == "Svart") {
    appendChatMessage(`Vita pjäserna vinner!`);
    winner = "white";
  } else if (result == "Vit") {
    appendChatMessage(`Svarta pjäserna vinner!`);
    winner = "black";
  } else if (result == "draw") {
    appendChatMessage(`Det är oavgjort!`);
    winner = "draw";
  }
  socket.emit("finished-game", { pgn: game.pgn(), id: room, result: winner });
}

function updateStatus() {
  var status = "";
  if (started == true) {
    var moveColor = "Vit";
    if (game.turn() === "b") {
      moveColor = "Svart";
    }
    if (game.in_checkmate()) {
      status = "Matchen är slut, " + moveColor + " sitter i schackmatt";
      if (finished == false) {
        finishedGame(moveColor);
      }
    } else if (game.in_draw()) {
      status = "Matchen är slut, det slutade oavgjort";
      if (finished == false) {
        finishedGame("draw");
      }
    } else {
      status = moveColor + "a pjäsernas drag";
      if (game.in_check()) {
        status += ", " + moveColor + " sitter i schack";
      }
      console.log(status);
    }

    $status.html(status);
    $fen.html(game.fen());
    $pgn.html(game.pgn());
  }
}

function joinGame(game_data) {
  started = true;
  finished = false;
  game = new Chess();
  messages.innerHTML = "";
  room = `${game_data["id"]}`;
  if (game_data["white_pieces_userid"] == user["id"]) {
    board.orientation("white");
    team = "white";
    chess_opponent_id = game_data["black_pieces_userid"];
    appendChatMessage(`Motståndare hittad! Du spelar med de vita pjäserna!`);
  } else {
    board.orientation("black");
    team = "black";
    chess_opponent_id = game_data["white_pieces_userid"];
    appendChatMessage(`Motståndare hittad! Du spelar med de svarta pjäserna!`);
  }

  socket.emit("request_opponent_username", chess_opponent_id);
  game.load(game_data["chessboard_state"]);
  board.position(game_data["chessboard_state"]);
  console.log("found a game!");
  updateStatus();
}

function appendChatMessage(msg) {
  var item = document.createElement("li");
  item.textContent = msg;
  messages.appendChild(item);
}

var reqGameBtn = document.getElementById("joinGame");
reqGameBtn.onclick = function () {
  appendChatMessage("Söker efter en motståndare...");
  socket.emit("request_user");
  socket.emit("request_game");
};

socket.on("connect", function () {
  console.log("Now connected to the server!");
  //   socket.emit("get_board", { game_id: "{{ game.id }}" });
});

socket.on("request_game_response", function (data) {
  joinGame(data);
});

socket.on("request_opponent_username_response", function (data) {
  chess_opponent_username = data;
  appendChatMessage(`Du möter: ${chess_opponent_username}`);
});

socket.on("request_user_response", function (data) {
  user = data;
});

socket.on("message", function (data) {
  console.log(data);
});

form.addEventListener("submit", function (e) {
  e.preventDefault();
  if (input.value) {
    socket.emit("send-chat-message", {
      input: `${user["username"]}: ${input.value}`,
      room: room,
    });
    input.value = "";
  }
});

socket.on("chat-message", function (msg) {
  appendChatMessage(msg);
});

// update the board when a move is made
socket.on("move", function (data) {
  console.log(`Move from: ${data["from"]} to ${data["to"]}`);
  console.log(
    game.move({ from: data["from"], to: data["to"], promotion: "q" })
  );
  board.position(game.fen());
  updateStatus();
});
