import socket
from select import select
import time
import utilz

sockets = []
clients = []


def new_client(server_socket):
    client_socket, addr = server_socket.accept()
    sockets.append(client_socket)
    clients.append(client_socket)
    print(f'New connection from: {addr}')


def recv_msg(cs):
    try:
        req = utilz._recv_msg(cs, utilz.HEADER_SIZE)
        if not req:
            close_conn(cs)
            return False

        print(f'{req=}')

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
        return False

    if body['type'].value == 0:
        return utilz.msg_content(0, body['name'], 'Welcome to the server, {name}')
    elif body['type'].value == 1:
        return utilz.msg_content(1, body['name'], body["msg"])
    elif body['type'].value == 2:
        close_conn(cs)
        return utilz.msg_content(2, body['name'], 'User {name} disconnected')
    elif body['type'].value == 4:
        return utilz.msg_content(4)


def close_conn(cs):
    print(f'Socket {cs} closed')
    clients.remove(cs)
    sockets.remove(cs)
    cs.close()


def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((utilz.HOST, utilz.PORT))
    server_socket.listen()
    sockets.append(server_socket)
    while True:
        try:
            read, _, warn = select(sockets, [], sockets)

            for sock in read:
                if sock == server_socket:
                    new_client(sock)
                elif (msg := recv_msg(sock)):
                    print(f'Message to send: {msg}')
                    for c in clients:
                        if c == sock and int(msg.decode()[0]) != 0 or int(msg.decode()[0]) == 4:
                            continue
                        try:
                            c.send(msg)
                        except:
                            close_conn(c)

            for sock in warn:
                close_conn(c)
        except:
            print('\nServer closed finally')
            break


server()
