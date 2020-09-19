import socket
import threading
import json
from datetime import datetime

HOST = 'localhost'
PORT = 5003
HEADER_SIZE = 10

clients = []


def new_client(server_socket):
    while True:
        client_socket, _ = server_socket.accept()
        clients.append(client_socket)
        threading.Thread(target=recv_msg, args=(client_socket, )).start()

def send_all(msg, cs):
    for c in clients:
        if c == cs: continue
        header = f'{len(msg[1]):<{HEADER_SIZE}}'.encode()
        try:
            c.send(header + msg[1])
        except:
            clients.remove(c)

def recv_msg(cs):
    while True:
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
            send_all((0, f'Welcome to the server, {data["name"]}'.encode()), cs)
        elif data_type == 1:
            send_all((1, f'<{datetime.now().strftime("%H:%M")}> [{data["name"]}]: {data["msg"]}'.encode()), cs)
        elif data_type == 2:
            send_all((2, f'User {data["name"]} disconnected'.encode()), cs)

def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    threading.Thread(target=new_client, args=(server_socket, )).start()

server()
