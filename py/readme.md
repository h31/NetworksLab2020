# Description

Using python to write a simple program multiple chats.

Client has to enter a name to use:

- Name limited by ```32``` characters 

- If the client doesn't enter his name. It will be ```default: anony ```

- Name of client will be changed into: ```name + randint(100)```. It will random until the name of clients is different

Message:
- A message from client will include``` message's length, message's type, and message```.

- A message from server only has ```message and its length```.

- Can send a large text (```max=9999``` characters).

First, client sends the client's name to server(```type=2```). Server will send a welcome message to the others. Normal message have ```type=1``` Clients can quit chat by entering ```!q``` or press ```Ctrl+C```, it will send a message (```type=0```) to server before programs are closed. Server will notify to the others. Server can close by ```Ctrl+C```, server will send signal ```-1``` to client before close, client will be closed too.