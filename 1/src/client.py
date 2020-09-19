import socket
import threading
import json
import sys

HOST = 'localhost'
PORT = 5003
HEADER_SIZE = 10


def msg_content(t, name, msg=''):
    msg_data = {
        'name': name,
    }
    if t == 1:
        msg_data['msg'] = msg
    msg_data = json.dumps(msg_data).encode()
    header = f'{t}{len(msg_data):<{HEADER_SIZE-1}}'.encode()
    return header + msg_data

def send_msg(cs, name):
    while True:
        msg = input()
        if not msg:
            sys.exit(1)
        if msg[0] == '\\':
            if msg[1] == 'q':
                cs.send(msg_content(2, name))
                cs.close()
                sys.exit()
            continue
        cs.send(msg_content(1, name, msg))


def recv_msg(cs):
    while True:
        try:
            req = cs.recv(HEADER_SIZE)
            if not req:
                sys.exit(1)
            msg = cs.recv(int(req.decode().strip()))
            print(msg.decode())
        except Exception as e:
            continue


def client():
    name = input('Your nickname: ')
    cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cs.connect((HOST, PORT))
    cs.send(msg_content(0, name))
    threading.Thread(target=send_msg, args=(cs, name)).start()
    threading.Thread(target=recv_msg, args=(cs,)).start()


client()
