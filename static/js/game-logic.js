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
    promotion: "q", // NOTE: always promote to a queen for example simplicity
  });

  // illegal move
  if (move === null) return "snapback";

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

function joinGame(game_data) {
  game.load(game_data.chessboard_state);
  board.position(game_data.chessboard_state);
  socket.emit("join", { room: `${game_data.id}` });
  console.log(`Succesefully joined room ${game_data.id}!`);
}

requesting_game = false;

socket.on("connect", function () {
  console.log("Now connected to the server!");
  console.log("Requesting game from server.");
  socket.emit("request_game");
  requesting_game = true;
  //   socket.emit("get_board", { game_id: "{{ game.id }}" });
});

socket.on("request_game_response", function (data) {
  if (requesting_game) {
    joinGame(data);
  }
  requesting_game = false;
});

// handle the form submit event to make a move
function makeMove() {
  var move = document.getElementById("move-input").value;
}

// update the board when a move is made
socket.on("move", function (data) {
  board.position(data);
});
