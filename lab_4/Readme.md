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

Message types for mail system:
 00 - Sign in
 01 - Sign up
 02 - Create an order
 03 - Confirm buy
 04 - View history of buyer
 05 - View sales history
 07 - View list items at store
 08 - View list store
 09 - Disconnect

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

Message types for mail system:

0 - Sign in
1 - Sign up
2 - Write mail
3 - View sent box
4 - View received box
5 - Read mail
6 - View list user
7 - Disconnect

To launch server:

```
python3 server-mail.py
```