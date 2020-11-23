import errno
import socket
from datetime import datetime
from select import select

HEADER_LENGTH = 10

IP = '0.0.0.0'
# IP = 'localhost'
PORT = 5454
CODE = 'utf-8'

clients = {}
socket_list = []


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((IP, PORT))
    server_socket.setblocking(False)
    server_socket.listen()
    socket_list.append(server_socket)
    print(f'Listening for connections on {IP}:{PORT}...')
    server(server_socket)


def client_connect(sock):
    client_socket, client_address = sock.accept()
    client_socket.setblocking(False)
    user = receive_header_and_message(client_socket)
    if user is False:
        return
    socket_list.append(client_socket)
    clients[client_socket] = user
    print(f"New connection from {client_address[0]}:{client_address[1]}, Username: {user['data'].decode(CODE)}")


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


def server(sock):
    try:
        while True:
            read_sockets, write_sockets, exception_sockets = select(socket_list, [], socket_list)
            for read_socket in read_sockets:
                if read_socket == sock:
                    client_connect(sock)
                else:
                    message = receive_header_and_message(read_socket)
                    if message is False:
                        try:
                            print(f'Closed connection from: {clients[read_socket]["data"].decode(CODE)}')
                            del clients[read_socket]
                            socket_list.remove(read_socket)
                            read_socket.shutdown(socket.SHUT_RDWR)
                            read_socket.close()
                            continue
                        except:
                            continue

                    message_time = datetime.utcnow().strftime("%d-%m-%Y %H:%M:%S").encode(CODE)
                    time_header = f"{len(message_time):<{HEADER_LENGTH}}".encode(CODE)
                    time = {"header": time_header, "data": message_time}
                    user = clients[read_socket]

                    server_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    print(f'{server_time} Message from {user["data"].decode(CODE)}: {message["data"].decode(CODE)}')
                    for client_socket in clients:
                        if client_socket != read_socket:
                            client_socket.send(user['header'] + user['data'] + message['header'] + message['data'] + time[
                                'header'] + time['data'])
    except KeyboardInterrupt:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
        exit(0)


if __name__ == '__main__':
    main()
