import logging
import socket
import threading

HOST = '127.0.0.1'
PORT = 8080
HEADER_LENGTH = 10
USERS_EXPECTED_NUMBER = 10


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(USERS_EXPECTED_NUMBER)
    print('Listening for connections...')

    connections = []
    connecting = False

    def _connect_users():
        nonlocal connecting
        for user in range(USERS_EXPECTED_NUMBER):
            conn, addr = server_socket.accept()

            if conn not in connections:
                connections.append(conn)
                threading.Thread(target=_send_data, args=(len(connections) - 1,)).start()
            connecting = True
            print(f'user n.{len(connections)} with address {addr} is connected')
            connecting = False
            threading.Thread(target=_connect_users).start()

    def _send_data(user):
        while True:
            try:
                data_header = connections[user].recv(HEADER_LENGTH)
                if not len(data_header):
                    print('No more data from the client')
                    connections[user].close()
                    return False

                data_length = int(data_header.decode('utf-8').strip())
                data = connections[user].recv(data_length).decode('utf-8')
                for each in range(len(connections)):
                    connections[each].send(data_header + data.encode('utf-8'))
                if not data or connecting:
                    break
            except ConnectionResetError as ex:
                logging.error(ex)
                connections[user].close()
                print(f'user n.{user + 1} has been disconnected')
                connections.remove(connections[user])
                return False

    threading.Thread(target=_connect_users).start()

    while True:
        pass


if __name__ == '__main__':
    main()
