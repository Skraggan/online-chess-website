const express = require('express');
const app = express();
const http = require('http');
const server = http.createServer(app);
const { Server } = require("socket.io");
const io = new Server(server);

app.get('/', (req, res) => {
  res.sendFile(__dirname + '/index.html');
});

io.on('connection', (socket) => {
  let username = "user"

  io.emit("chat message", `${username} connected`)
  socket.on("disconnect", () => {
    io.emit("chat message", `${username} disconnected`)
  })

  socket.on("chat command", (msg) => {
    msg = msg.slice(1)
    args = msg.split(" ")
    if (args[0].toLowerCase() == "username") {
      io.emit("chat message", `${username} changed name to ${args[1]}`)
      username = args[1]
    }
  })

  socket.on("chat message", (msg) => {
    msg = `${username}: ` + msg
    io.emit("chat message", msg)  
  })
});

server.listen(3000, () => {
  console.log('listening on *:3000');
});