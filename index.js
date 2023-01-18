const express = require('express');
const app = express();
const http = require('http');
const server = http.createServer(app);
const { Server } = require("socket.io");
const io = new Server(server);

let users = {}
let random_user_count = 1
let users_typing = []

app.get('/', (req, res) => {
  res.sendFile(__dirname + '/index.html');
});

io.on('connection', (socket) => {
  
  users[socket.id] = {username: `User ${random_user_count}`}
  random_user_count++
  let username = users[socket.id].username
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
      users[socket.id].username = username
    }
  })
 
  socket.on("chat message", (msg) => {
    msg = `${username}: ` + msg
    socket.broadcast.emit("chat message", msg)  
    console.log(users)
  })

  socket.on("user typing", (msg) => {
    console.log("User typed: " + msg);
  });


  socket.on("user typing", (user, state) => {
    console.log(user);
      console.log("user typing")
    user_id = user.id
    if (state == true) {
      if (user_id in users_typing){}
      else {users_typing.push(user_id)}
    } else {
      if (user_id in users_typing){users_typing.splice((users_typing.indexOf(user_id)), 1)}
    }
    // console.log(user_id)
  })
});

server.listen(3000, () => {
  console.log('listening on *:3000');
});