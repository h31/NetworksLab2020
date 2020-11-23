import errno
import socket
import threading
from datetime import datetime
from tzlocal import get_localzone

HEADER_LENGTH = 10

IP = "51.15.130.137"
# IP = "localhost"
PORT = 5454
CODE = 'utf-8'


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


def receive_header_and_message(sock):
    length = receive_header(sock)
    header_and_message = receive_message(sock, length)
    return header_and_message


def receive_header(sock):
    try:
        message_header = sock.recv(HEADER_LENGTH)
        if not len(message_header):
            return False
        message_length = int(message_header.decode(CODE))
        return message_length
    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            return False


def receive_message(sock, message_length):
    message = b""
    if not message_length:
        return False
    while True:
        try:
            while message_length != len(message):
                message += sock.recv(message_length - len(message))
            return {'header': f"{len(message):<{HEADER_LENGTH}}".encode(CODE), 'data': message}
        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                return False
            continue
        except:
            return False


def send(sock):
    while True:
        try:
            message = input()
            if message:
                try:
                    if message == "\exit":
                        sock.shutdown(socket.SHUT_RDWR)
                        sock.close()
                        exit(0)
                except:
                    exit(0)

                message = message.encode(CODE)
                message_header = f"{len(message):<{HEADER_LENGTH}}".encode(CODE)
                sock.send(message_header + message)
        except EOFError or KeyboardInterrupt:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            exit(0)
        except:
            print('Closed connection')
            exit(0)
            return


def receive(sock):
    tz = get_localzone()
    while True:
        try:
            username = receive_header_and_message(sock)["data"].decode(CODE)
            message = receive_header_and_message(sock)["data"].decode(CODE)
            message_time = receive_header_and_message(sock)["data"].decode(CODE)
            client_time = datetime.strptime(message_time, "%d-%m-%Y %H:%M:%S").now(tz).strftime("%d-%m-%Y %H:%M:%S")
            print(f'<{client_time}>[{username}]: {message}')
        except:
            exit(0)
            return


if __name__ == '__main__':
    main()
