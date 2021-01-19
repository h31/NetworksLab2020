# Protocol description

## Food client

Requests to server include 2 parts:

1. Header 4 symbols: Store the size of message.
2. Message in type json: type request and the information corresponding to the request.

User need to sign up/sign in (if you already have an account) before using the application.

In application, user can choose role seller or buyer.

Activities for buyer:

- Order items in the store buy give name of store, buyer's location and list items, it will show the items, that already have in the store, the lacks items and its prices. 
- View the history of buying
- View list of store in system
- View list of products in a specific store
- Disconnect from server

Activities for seller:

- Add an new store with its location,  items and prices. Store create buy a seller will belong to him
- View sales history
- View list of store in system
- Disconnect from server

To launch the client application:

```
python3 food-client.py host port
```

## Server mail

Server will receive request from client, which include 2 parts:

1. Header 8 symbols: Store the size of message.
2. Message in type json: type request and the information corresponding to the request.

Server receive mail from users  and store into database information about sender, receiver, header and content of mail.

Server allows user to view the inbox and outbox.

Server allows user to read mail through header of mail.

Server allows user to view list user.

Server receive request sign out and close the connection of client.

To launch server:

```
python3 server-mail.py
```