import socket
import sys
import threading
from datetime import datetime

HEADER = 64
PORT = 8080
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER_MASSAGE = "SERVER DEAD"
dict = {}
dictConn = []

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)


def print_time(addr, msg):
    return (f"<{str(datetime.now().hour)}:{str(datetime.now().minute)}>" \
            f" [{dict.get(addr[1])}] {msg}")


def print_name(addr, msg):
    return f" [{dict.get(addr[1])}] {msg}"


def registration(conn, addr, msg):
    dict.setdefault(addr, msg)
    dictConn.append(conn)


def send_all_world(conn, addr, msg):
    for i in dictConn:
        if i == conn:
            continue
        i.send((f"[{dict.get(addr[1])}] {msg}").encode(FORMAT))


def send_all_world_server(msg):
    for i in dictConn:
        i.send((msg).encode(FORMAT))


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg == DISCONNECT_MESSAGE:
                try:
                    send_all_world(conn, addr, msg)
                    dictConn.remove(conn)
                    print('this person remove')
                except:
                    connected = False
                    print("Server is dead.")
            elif msg == SERVER_MASSAGE:
                connected = False
                dictConn.remove(conn)
            elif addr[1] not in dict.keys():
                registration(conn, addr[1], msg)
                conn.send(print_name(addr, msg).encode(FORMAT))
            else:
                print(print_time(addr, msg))
                send_all_world(conn, addr, msg)
                conn.send(print_name(addr, msg).encode(FORMAT))
    conn.close()


def listen_server():
    textServer = input()
    if textServer == 'quit':
        print(textServer)
        msg = 'Server was closed'
        send_all_world_server(msg)
        send_all_world_server(DISCONNECT_MESSAGE)
        dict.clear()
        dictConn.clear()
        server.close()
        start(False)

def start(check):
    while check:
        try:
            server.listen(5)
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
        except:
            sys.exit(0)



if __name__ == '__main__':
    thread2 = threading.Thread(target=listen_server)
    thread2.start()
    print("[STARTING] server is starting...")
    print(f"[LISTENING] Server is listening on {SERVER}")
    start(True)