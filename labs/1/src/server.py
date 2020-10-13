import socket
import threading
from datetime import datetime
import utilz

clients = []

def new_client(server_socket):
    while True:
        client_socket, addr = server_socket.accept()
        clients.append(client_socket)
        print(f'New connection from: {addr}')
        threading.Thread(target=recv_msg, args=(client_socket, )).start()


def send_all(cs, msg):
    print(f'Message to send: {msg}')
    for c in clients:
        if c == cs and int(msg.decode()[0]) != 0 or int(msg.decode()[0]) == 4:
            continue
        try:
            c.send(msg)
        except:
            clients.remove(c)
            c.close()


def recv_msg(cs):
    while True:
        try:
            req = utilz._recv_msg(cs, utilz.HEADER_SIZE)

            if not req:
                cs.close()
                break

            header = utilz.Header(req)
            body = {
                'type': header.type,
            }

            for _type, size in header.type_to_len:
                data = b''
                print(f'{_type=} {size=}')
                while len(data) < size:
                    data += cs.recv(size-len(data))
                body[_type] = data.decode()
        except:
            break

        if body['type'].value == 0:
            send_all(cs, utilz.msg_content(0, body['name'], 'Welcome to the server, {name}'))
        elif body['type'].value == 1:
            send_all(cs, utilz.msg_content(1, body['name'], body["msg"]))
        elif body['type'].value == 2:
            send_all(cs, utilz.msg_content(2, body['name'], 'User {name} disconnected'))
            cs.close()
            break
        elif body['type'].value == 4:
            continue


def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((utilz.HOST, utilz.PORT))
    server_socket.listen()
    threading.Thread(target=new_client, args=(server_socket, )).start()


server()
