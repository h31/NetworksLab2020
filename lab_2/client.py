import socket
import sys
import threading
import time
from header_settings import *

# settings
IP = '127.0.0.1'
PORT = 7777
CODE = 'utf-8'


def client():
    nickname = input('Enter your nickname: ')
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client_socket.connect((IP, PORT))
    print('Connection was established')

    # organize threads for read and write

    read_thread = threading.Thread(target=read, args=(client_socket, )).start()
    write_thread = threading.Thread(
        target=write, args=(client_socket, nickname, )).start()


def get_local_time(sec):
    return time.strftime('%d.%m %H:%M:%S', time.localtime(sec))


def write(client_socket, nickname):
    while True:
        try:
            message = input('Enter message: ')

            if message == '-leave':
                print('You closed the connection')
                header = ''
                client_socket.send(header.encode(CODE))
                # sending empty header and closing connection
                client_socket.shutdown(socket.SHUT_RDWR)
                client_socket.close()
                return

            if message:  # it is not empty
                message = message.encode(CODE)
                header = f"{len(message):<{H_LEN_CHAR}}{nickname:<{H_NAME_CHAR}}".encode(CODE)
                client_socket.send(header + message)
        except Exception as e:
            print(e)
            return


def wait_full_length(socket, content, length):
    while len(content) < length:
        content += socket.recv(length - len(content))
        if length == len(content):
            break


def read(client_socket):
    while True:
        try:
            header = client_socket.recv(SERVER_HEADER_LENGTH)

            if not len(header):
                print('Connection was closed by server.')
                return

            # while len(header) < SERVER_HEADER_LENGTH:
            #     header += client_socket.recv(SERVER_HEADER_LENGTH -
            #                                  len(header))
            #     if len(header) == SERVER_HEADER_LENGTH:
            #         break

            wait_full_length(client_socket, header, SERVER_HEADER_LENGTH)

            header = header.decode(CODE)

            h_charcount = header[:H_LEN_CHAR]
            h_nickname = header[H_LEN_CHAR:H_LEN_CHAR+H_NAME_CHAR].strip()
            h_time = header[H_LEN_CHAR+H_NAME_CHAR:].strip()

            h_charcount = int(h_charcount)
            h_time = int(h_time)

            message = client_socket.recv(h_charcount)

            # while h_charcount > len(message):
            #     message += client_socket.recv(h_charcount - len(message))
            #     if h_charcount == len(message):
            #         break

            wait_full_length(client_socket, message, h_charcount)

            message = message.decode(CODE)
            print(f"<{get_local_time(h_time)}> [{h_nickname}]: {message}")

        except Exception as e:
            print(f"Error {e}")
            return


client()
