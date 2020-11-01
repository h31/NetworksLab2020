import socket
import threading
from datetime import datetime


HEADER_LENGTH = 16

# IP = '0.0.0.0'
IP = 'localhost'
PORT = 5454
CODE = 'utf-8'

clients = {}


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((IP, PORT))
    server_socket.listen()
    print(f'Listening for connections on {IP}:{PORT}...')
    while True:
        client_socket, client_address = server_socket.accept()
        user = receive_message(client_socket)
        if user is False:
            continue
        clients[client_socket] = user
        print(f"New connection from {client_address[0]}:{client_address[1]}, Username: {user['data'].decode(CODE)}")
        threading.Thread(target=server, args=(client_socket,)).start()


def receive_message(sock):
    try:
        message_header = sock.recv(HEADER_LENGTH)
        if not len(message_header):
            return False
        message_length = int(message_header.decode(CODE))
        return {'header': message_header, 'data': sock.recv(message_length)}
    except:
        return False


def server(sock):
    while True:
        message = receive_message(sock)

        if message is False:
            try:
                print(f'Closed connection from: {clients[sock]["data"].decode(CODE)}')
                del clients[sock]
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()
                continue
            except:
                continue

        message_time = datetime.utcnow().strftime("%d-%m-%Y %H:%M:%S").encode(CODE)
        time_header = f"{len(message_time):<{HEADER_LENGTH}}".encode(CODE)
        time = {"header": time_header, "data": message_time}
        user = clients[sock]

        server_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        print(f'{server_time} Message from {user["data"].decode(CODE)}: {message["data"].decode(CODE)}')
        for client_socket in clients:
            if client_socket != sock:
                client_socket.send(user['header'] + user['data'] + message['header'] + message['data'] + time[
                        'header'] + time['data'])


if __name__ == '__main__':
    main()
