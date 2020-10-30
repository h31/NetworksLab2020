import socket
from select import select
import time
import utilz

sockets = []
clients = {}


def new_client(server_socket):
    client_socket, addr = server_socket.accept()
    sockets.append(client_socket)
    client_socket.setblocking(False)
    clients[client_socket] = dict()
    print(f'New connection from: {addr}')


def recv_msg(cs):
    try:
        if not clients[cs].get('header'):
            header_data = clients[cs].get('header_data', b'')
            clients[cs]['header_data'] = header_data + cs.recv(utilz.HEADER_SIZE - len(header_data))
            if len(clients[cs]['header_data']) < utilz.HEADER_SIZE:
                return False

            print(f'{clients[cs]["header_data"]=}')

            clients[cs]['header'] = utilz.Header(clients[cs]['header_data'].decode())
            del clients[cs]['header_data']

        header = clients[cs]['header']
        body_data = clients[cs].get('body_data', b'')
        clients[cs]['body_data'] = body_data + cs.recv(header.total_size - len(body_data))
        if len(clients[cs]['body_data']) < header.total_size:
            return False

        print(f'{clients[cs]["body_data"]=}')

        body = {
            'type': header.type
        }

        offset = 0
        for _type, size in header.type_to_len:
            print(f'{offset=}\t{size=}')
            body[_type] = clients[cs]['body_data'][offset:offset+size].decode()
            offset += size

        print(f'{body=}')

        del clients[cs]['header']
        del clients[cs]['body_data']
    except:
        return False

    if body['type'].value == 0:
        return utilz.msg_content(0, body['name'], 'Welcome to the server, {name}')
    elif body['type'].value == 1:
        return utilz.msg_content(1, body['name'], body['msg'])
    elif body['type'].value == 2:
        close_conn(cs)
        return utilz.msg_content(2, body['name'], 'User {name} disconnected')
    elif body['type'].value == 4:
        return utilz.msg_content(4)


def close_conn(cs):
    print(f'Socket {cs} closed')
    del clients[cs]
    sockets.remove(cs)
    cs.close()


def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((utilz.HOST, utilz.PORT))
    server_socket.listen()
    server_socket.setblocking(False)
    sockets.append(server_socket)
    while True:
        try:
            read, _, warn = select(sockets, [], sockets)

            for sock in read:
                if sock == server_socket:
                    new_client(sock)
                elif (msg := recv_msg(sock)):
                    print(f'Message to send: {msg}')
                    for cs in clients:
                        if cs == sock and int(msg.decode()[0]) != 0 or int(msg.decode()[0]) == 4:
                            continue
                        try:
                            cs.send(msg)
                        except:
                            close_conn(cs)

            for sock in warn:
                close_conn(sock)
        except Exception as e:
            print(e)
            print('\nServer closed finally')
            break


server()
