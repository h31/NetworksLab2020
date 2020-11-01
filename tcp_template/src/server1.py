import threading
import socket

HEADER_LENGTH = 16

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# server.bind(('0.0.0.0', 1234))
server.bind(('127.0.0.1', 1234))
server.listen(7)
print('Server is online')

clients_sockets = {}


def send_data(current_client, header, data):
    for client in clients_sockets.values():
        if client != current_client:
            client.sendall(header + data)


def close_connection(user_address):
    clients_sockets[user_address].shutdown(socket.SHUT_WR)
    clients_sockets[user_address].close()
    del clients_sockets[user_address]
    print(f'Client {user_address} disconnected')


def receive_bytes(client, length):
    received = 0
    message = b''
    while True:
        try:
            data = client.recv(length - received)
            if received < length:
                message += data
                received += len(data)
            elif message == b'':
                print(f"message is empty: {message}")
                close_connection(client)
            else:
                return message
        except Exception as ex:
            return


def listen_socket(user_address):
    user = clients_sockets[user_address]
    while True:
        try:
            data = user.recv(HEADER_LENGTH)
            if data == b'':
                close_connection(user_address)
            else:
                message_length = int(data.decode('utf-8').strip())
                print(f"message length: {message_length}")
                message = receive_bytes(user, message_length)
                if not message:
                    print("error")
                else:
                    send_data(user, data, message)
        except Exception as ex:
            return


def accept_sockets():
    while True:
        client, addr = server.accept()
        print(f"User [{addr}] connected")
        clients_sockets[addr] = client
        threading.Thread(target=listen_socket, args=(addr,)).start()


def main():
    threading.Thread(target=accept_sockets).start()


if __name__ == '__main__':
    main()

