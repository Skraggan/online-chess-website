const express = require('express');
const app = express();
const http = require('http');
const server = http.createServer(app);
const { Server } = require("socket.io");
const io = new Server(server);

var nickname = "user"

app.get('/', (req, res) => {
  res.sendFile(__dirname + '/index.html');
});

io.on('connection', (socket) => {
  io.emit("chat message", "user connected")
  socket.on("disconnect", () => {
    io.emit("chat message", "user disconnected")
  })

  socket.on("chat command", (msg) => {
    msg = msg.slice(1)
    args = msg.split(" ")
    if (args[0].toLowerCase() == "nickname") {
      nickname = args[1]
    }
  })

  socket.on("chat message", (msg) => {
    io.emit("chat message", msg)
  })
});

server.listen(3000, () => {
  console.log('listening on *:3000');
});