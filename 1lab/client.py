import socket
import threading
import time
from datetime import datetime
from math import ceil
from tzlocal import get_localzone


HEADER_LENGTH = 16

IP = "51.15.130.137"
# IP = "localhost"
PORT = 5454
CODE = 'utf-8'
LENGTH_PART = 500


def main():
    my_username = nick()
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_sock.connect((IP, PORT))
    username = my_username.encode(CODE)
    username_header = f"{len(username):<{HEADER_LENGTH}}".encode(CODE)
    client_sock.send(username_header + username)
    threading.Thread(target=send, args=(client_sock,)).start()
    threading.Thread(target=receive, args=(client_sock,)).start()


def nick():
    while True:
        nickname = input("Username: ")
        if not nickname:
            print("Please enter username!")
            continue
        return nickname


def receive_message(sock):
    while True:
        try:
            message_header = sock.recv(HEADER_LENGTH)
            if not len(message_header):
                return False
            message_length = int(message_header.decode(CODE))
            return {'header': message_header, 'data': sock.recv(message_length)}
        except:
            return


def send(sock):
    while True:
        try:
            message = input()
            try:
                if message == "\exit":
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()
                    exit(0)
            except:
                exit(0)

            if message:
                if len(message) > LENGTH_PART:
                    length = ceil(len(message) / LENGTH_PART)
                    i = 0
                    while i < length:
                        part = message[i * LENGTH_PART: (i + 1) * LENGTH_PART]
                        message_send = str(part).encode(CODE)
                        message_header = f"{len(message_send):<{HEADER_LENGTH}}".encode(CODE)
                        sock.send(message_header + message_send)
                        i += 1
                        time.sleep(0.1)
                else:
                    message = message.encode(CODE)
                    message_header = f"{len(message):<{HEADER_LENGTH}}".encode(CODE)
                    sock.send(message_header + message)
        except KeyboardInterrupt:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            exit(0)
            return
        except:
            print('Closed connection')
            exit(0)
            return


def receive(sock):
    tz = get_localzone()
    while True:
        try:
            username = receive_message(sock)["data"].decode(CODE)
            message = receive_message(sock)["data"].decode(CODE)
            message_time = receive_message(sock)["data"].decode(CODE)
            client_time = datetime.strptime(message_time, "%d-%m-%Y %H:%M:%S").now(tz).strftime("%d-%m-%Y %H:%M:%S")
            print(f'<{client_time}>[{username}]: {message}')
        except:
            exit(0)
            return


if __name__ == '__main__':
    main()
