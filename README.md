# NetworksLab2020
`Client.py` - client app;
`Server.py` - Server app;

### Protocol description:
1. **Header** (10 symbols). Stores the size of the *content*; 
2. **Content** (up to maximum symbols number can be stored in header). Message parts are devided by zero symbol (`\0`)
    1. **_Nickname_** 
    2. **_Send datum_** 
    3. **_Message content_** (user's text)
    

In the client app, user is required to type his nickname in. After that one can start chatting with other users.

*Linux* and *Windows* OS support (both tested).

Time of message sent transofrms to user's local time.

All 3 parts of messages are highlightes with different colors.

Empty messsages (new lines) are not sent to the server.

Exit the application by typing `exit` in.

The server differentiates among the users by their addresses.

When a client disconnects, a server shuts the corresponding connection down and closes the client's socket.
