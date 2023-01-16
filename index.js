const express = require('express');
const app = express();
const http = require('http');
const server = http.createServer(app);
const { Server } = require("socket.io");
const io = new Server(server);

let users = {}
let usernames = {}

app.get('/', (req, res) => {
  res.sendFile(__dirname + '/index.html');
});

io.on('connection', (socket) => {
  let username
  users[socket.id] = {username: "Unknown User"}

  if (socket.id in usernames){
    username = usernames[socket.id]
  } else {
   username = "Unknown User" 
  }
  
  // console.log(socket)

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
      usernames[socket.id] = username
    }
  })
 
  socket.on("chat message", (msg) => {
    msg = `${username}: ` + msg
    socket.broadcast.emit("chat message", msg)  
    console.log(usernames)
  })
});

server.listen(3000, () => {
  console.log('listening on *:3000');
});