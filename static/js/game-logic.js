var board = null;
var game = new Chess();
var $status = $("#status");
var $fen = $("#fen");
var $pgn = $("#pgn");

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

  socket.emit("move", { from: source, to: target, room: room });
  console.log(`history: ${game.history()}`);

  updateStatus();
}

// update the board position after the piece snap
// for castling, en passant, pawn promotion
function onSnapEnd() {
  board.position(game.fen());
}

function updateStatus() {
  var status = "";

  var moveColor = "White";
  if (game.turn() === "b") {
    moveColor = "Black";
  }

  // checkmate?
  if (game.in_checkmate()) {
    status = "Game over, " + moveColor + " is in checkmate.";
  }

  // draw?
  else if (game.in_draw()) {
    status = "Game over, drawn position";
  }

  // game still on
  else {
    status = moveColor + " to move";

    // check?
    if (game.in_check()) {
      status += ", " + moveColor + " is in check";
    }

    console.log(status);
  }

  $status.html(status);
  $fen.html(game.fen());
  $pgn.html(game.pgn());
}

var config = {
  draggable: true,
  position: "start",
  onDragStart: onDragStart,
  onDrop: onDrop,
  onSnapEnd: onSnapEnd,
};
board = Chessboard("board", config);

updateStatus();

var socket = io();

let team = null;
let room = null;

function joinGame(game_data) {
  console.log(game_data);
  if (game_data[2] == 1) {
    team = "white";
    console.log("Created a new game!");
    board.orientation("white");
  } else if (game_data[2] == 0) {
    console.log("Joined an existing game!");
    team = "black";
    board.orientation("black");
  }
  game.load(game_data[1]);
  board.position(game_data[1]);
  socket.emit("join", { room: `${game_data[0]}` });
  room = `${game_data[0]}`;
  console.log(`Succesefully joined room ${game_data[0]}!`);
}

requesting_game = false;

var reqGameBtn = document.getElementById("joinGame");
reqGameBtn.onclick = function () {
  console.log("Requesting game from server.");
  socket.emit("request_game");
  requesting_game = true;
};

socket.on("connect", function () {
  console.log("Now connected to the server!");
  //   socket.emit("get_board", { game_id: "{{ game.id }}" });
});

socket.on("request_game_response", function (data) {
  if (requesting_game) {
    console.log(`requested game respone: ${data}`);
    joinGame(data);
  }
  requesting_game = false;
});

socket.on("message", function (data) {
  console.log(data);
});

// update the board when a move is made
socket.on("move", function (data) {
  console.log(`Move from: ${data["from"]} to ${data["to"]}`);
  console.log(
    game.move({ from: data["from"], to: data["to"], promotion: "q" })
  );
  board.position(game.fen());
});
