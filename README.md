# NetworksLab2020
server.py - server app for first task
client.py - client app for first task 
server_poll.py - server app for second task
client_poll.py - client app for second task

Protocol description

At the start the client enters a name

Structure of message: local time[name]:message

The name must not exceed 2048 in length

Time format: HH.MM.SS

Before sending the name and message, the length of the name and message is sent respectively

