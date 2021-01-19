# FOOD ORDERING SERVER PROTOCOL

**Structure request**

1. Header 4 bytes: Store the size of message.
2. Message json: type request and the information corresponding to the request.

**Server will handle:**

- user sign in or sign up
- disconnect message
- request buy from buyer and confirm request buy
- request show all stores
- request show items in a store
- request show history buy of buyer and history sell of seller
- request add new store and items of seller
- Seller can see history of selling

**Message types for mail system:**
00 - Sign in
01 - Sign up
02 - Create an order
03 - Confirm buy
04 - View history of buyer
05 - View sales history
07 - View list items at store
08 - View list store
09 - Disconnect

# MAIL TRANSFER CLIENT PROTOCOL

**Structure request**

1. Header 8 bytes: Store the size of message.
2. Message json: type request and the information corresponding to the request.

**Client will send some requests:**

- user sign in or sign up
- disconnect from server
- send an new email
- show inbox
- show send box
- read an email
- show all users name

**Message types for mail system:**
0 - Sign in
1 - Sign up
2 - Write mail
3 - View sent box
4 - View received box
5 - Read an email
6 - View list user
7 - Disconnect
