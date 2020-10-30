import threading
import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('127.0.0.1', 8080))
server.listen(7)
print('Server is online')

clients_sockets = {}


def send_data(current_client, data):
    for client in clients_sockets.values():
        if client != current_client:
            client.sendall(data)


def close_connection(user_address):
    clients_sockets[user_address].shutdown(socket.SHUT_WR)
    clients_sockets[user_address].close()
    del clients_sockets[user_address]
    print(f'Client {user_address} disconnected')


def listen_socket(user_address):
    user = clients_sockets[user_address]
    while True:
        try:
            current_data = user.recv(2048)
        except ConnectionResetError:
            close_connection(user_address)
            return False
        except Exception:
            return False
        else:
            if current_data == b'':
                close_connection(user_address)
            else:
                send_data(user, current_data)


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

