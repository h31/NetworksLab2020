import socket
from select import select
import json
from datetime import datetime

HOST = 'localhost'
PORT = 5003
HEADER_SIZE = 10

sockets = []
clients = []

def new_client(server_socket):
    client_socket, _ = server_socket.accept()
    sockets.append(client_socket)
    clients.append(client_socket)

def recv_msg(cs):
    try:
        req = cs.recv(HEADER_SIZE)
    except:
        return False
    if not req:
        return False
    # 0 conn
    # 1 msg
    # 2 exit
    header = req.decode().strip()
    data_type = int(header[0])
    data = cs.recv(int(header[1::]))
    data = json.loads(data.decode())
    if data_type == 0:
        return (0, f'Welcome to the server, {data["name"]}'.encode())
    elif data_type == 1:
        return (1, f'<{datetime.now().strftime("%H:%M")}> [{data["name"]}]: {data["msg"]}'.encode())
    elif data_type == 2:
        return (2, f'User {data["name"]} disconnected'.encode())

def server():
    server_socket= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.setblocking(False)
    server_socket.listen()
    sockets.append(server_socket)
    while True:
        read, _, warn = select(sockets, [], sockets)

        for sock in read:
            if sock == server_socket:
                new_client(sock)
            elif (msg := recv_msg(sock)):
                for c in clients:
                    if msg[0] > 0 and c == sock: continue
                    header = f'{len(msg[1]):<{HEADER_SIZE}}'.encode()
                    try:
                        c.send(header + msg[1])
                    except:
                        sockets.remove(c)
                        clients.remove(c)

        for sock in warn:
            sockets.remove(c)
            clients.remove(c)

server()
