# pyTFTP
TFTP (Trivial File Transfer Protocol) client and server implementation
in Python.

## Features

The server and client divide the file into 512-byte packets to send in turn (max ). After receiving each packet, receiver send an acknowledgement packet to sender to receive the next packet (number of acknowledgement packet start from 1). If client request to send file to server, server will send acknowledgement packet number 0 to client.

## Usage
Client:
```
python3 client.py
```
After running client, you need to enter r (read request) or w (write request) and name of file.

Server:
```
python3 server.py
```
server bind to port 69 to receive request and another port to receive and send data packet or acknowledgement packet.