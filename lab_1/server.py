import socket
import time
import sys
import json
import threading

# settings
IP = '127.0.0.1'
PORT = 7777
CODE = 'utf-8'

# 16 symbols: 8 for length of message, 8 for nickname(only for test)
H_LEN_CHAR = 8  # how much char are in header for length of message
H_NAME_CHAR = 8  # nickname max len
H_TIME_CHAR = 16
HEADER_LENGTH = H_LEN_CHAR + H_NAME_CHAR

clients = []  # here will lay clients sockets


def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((IP, PORT))
    server_socket.listen()
    print(f"Listening for connections ip:{IP}, port:{PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        threading.Thread(target=new_connection, args=(
            client_socket, client_address, )).start()


def new_connection(client_socket, client_address):
    clients.append(client_socket)
    print(f"New connection from {client_address[0]}:{client_address[1]}")
    # make reciever for thread with this socket
    reciever(client_socket, client_address)


def get_message(client_socket):
    # when we get empty header - we close connection.
    while True:
        try:
            header = client_socket.recv(HEADER_LENGTH)
        except Exception:
            return

        if not header:
            return
            # it is that connection will be closed

        while len(header) < HEADER_LENGTH:
            header += client_socket.recv(HEADER_LENGTH - len(header))
            if len(header) == HEADER_LENGTH:
                break

        header = header.decode(CODE)
        h_charcount = header[:H_LEN_CHAR]

        try:
            int(h_charcount)
        except ValueError:
            print('Header has incorrect type. Must be int.')
            continue

        h_charcount = int(h_charcount)
        h_nickname = header[H_LEN_CHAR:].strip()

        message = client_socket.recv(h_charcount)

        while h_charcount > len(message):
            message += client_socket.recv(h_charcount - len(message))
            if h_charcount == len(message):
                break

        message = message.decode(CODE)

        return {"length": h_charcount, "nickname": h_nickname, "data": message}


def get_time(sec):
    return time.strftime('%d.%m %H:%M:%S', time.localtime(sec))


def reciever(client_socket, client_address):

    while True:
        # read message
        message = get_message(client_socket)
        recieve_time = int(time.time())
        server_formatted_time = get_time(recieve_time)

        if not message:
            client_socket.shutdown(socket.SHUT_WR)
            client_socket.close()
            print(f"Connection closed by client {client_address[0]}:{client_address[1]}")
            clients.remove(client_socket)
            return

        print(f"Recieved message from {message['nickname']} at {server_formatted_time}: {message['data']}")

        # get info for server that message has been recieved

        # send this message to all other clients

        header_to_send = f"{message['length']:<{H_LEN_CHAR}}{message['nickname']:<{H_NAME_CHAR}}{recieve_time:<{H_TIME_CHAR}}"
        message_to_send = header_to_send + message['data']
        message_to_send = message_to_send.encode(CODE)

        for client in clients:
            if client != client_socket:
                try:
                    client.send(message_to_send)
                except Exception:
                    client.close()
                    clients.remove(client)
                    continue


server()
