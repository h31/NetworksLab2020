# The Protocol Specifications

This is the client-server application running on TCP-sockets. 


## Connecting

After the server will accept client's connection, the server will send the information about its timezone, `UTC`-formatted
like `\2+0300`, `\2-1200`, which corresponds to `UTC +03:00`, `UTC -12:00`, etc. 

## Data format

The messages in this application looks as follows: `time\2username\2message\1`, where the `\1` is special symbol to determine the end of message, and `\2` are the symbols to distinguish header's parts.  
