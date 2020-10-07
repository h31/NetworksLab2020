import socket
import sys
import threading
from datetime import datetime

SERVER_MASSAGE = "SERVER DEAD"

HEADER = 64
PORT = 8080
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)


def read_listen(check):
    while True:
        if check == False:
            print('Enter any key to exit')
            send_server(DISCONNECT_MESSAGE)
            read_all_world(False)
            client.shutdown(socket.SHUT_WR)
            client.close()
            break
        else:
            msg = input()
            if msg == DISCONNECT_MESSAGE:
                print('you are disconnected from the server')
                send_server(DISCONNECT_MESSAGE)
                read_all_world(False)
                client.shutdown(socket.SHUT_WR)
                client.close()
                break
            else:
                send_server(msg)


def send_server(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    try:
        client.send(send_length)
        client.send(message)
    except:
        sys.exit(0)


def read_all_world(check):
    while check:
        try:
            data = client.recv(4096).decode(FORMAT)
            print(f"<{str(datetime.now().hour)}:{str(datetime.now().minute)}>" + data)
            if data == DISCONNECT_MESSAGE:
                read_listen(False)
        except:
            sys.exit(0)


clientText = input('Input your name:')
send_server(clientText)
potok = threading.Thread(target=read_all_world, args=(True,))
potok.start()

read_listen(True)
