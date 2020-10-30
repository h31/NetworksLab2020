# The Protocol Specifications

This is the client-server application running on TCP-sockets. There's two steps to work with this server: `connecting` and `transmitting`. 


## Connecting

After the server will accept client's connection, the client should **immediately** send the information about its timezone, `UTC`-formatted
like `\2+0300`, `\2-1200`, which corresponds to `UTC +03:00`, `UTC -12:00`, etc. The `\2` is the special symbol for server to identify that it is 
getting the information about the preceding connection's timezone. This information must be sent once immediately after server accepted the connection. 

## Transmitting

When the client is connected to the server, it can start sending data. The data `must` be formatted like: `\1<data>\1`, where the `\1` is the 
special symbol that allows the server to understand where the `data` starts and ends. Server receives data within `1024-byte` blocks. 
