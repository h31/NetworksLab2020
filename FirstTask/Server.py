import logging
import socket
import threading

from FirstTask.CustomSocket import CustomSocket

HOST = '127.0.0.1'
PORT = 8080
HEADER_LENGTH = 10
USERS_EXPECTED_NUMBER = 10


def main():
    server_socket = CustomSocket()
    server_socket.setsockopt()
    server_socket.bind(HOST, PORT)
    server_socket.listen(USERS_EXPECTED_NUMBER)
    print('Waiting for users...')

    connections = {}
    connecting = False

    def _connect_users():
        nonlocal connecting
        for user in range(USERS_EXPECTED_NUMBER):
            conn, addr = server_socket.accept()

            if conn not in connections:
                connections[addr] = conn
                threading.Thread(target=_send_data, args=(addr,)).start()

            print(f'user with address {addr} is connected')

            threading.Thread(target=_connect_users).start()

    def _send_data(user):
        while True:
            try:
                data_header, data = _receive_data(user)

                if not data_header or not data or connecting:
                    _close_user_connection(user)
                    return False

                for each in connections.values():
                    data_for_each = b'\0'.join([bytes(d, 'utf-8') for d in data])
                    each.send(data_header + data_for_each)
            except ConnectionResetError as ex:
                logging.error(ex)
                _close_user_connection(user)
                return False

    def _close_user_connection(user):
        connections[user].shutdown(socket.SHUT_WR)
        connections[user].close()
        print(f'user with address {user} has been disconnected')
        del connections[user]

    def _receive_data(user):
        data_header = server_socket.receive_bytes_num(HEADER_LENGTH, connections[user])
        if not data_header:
            return False, False
        data_length = int(data_header.decode().strip())
        data = server_socket.receive_bytes_num(data_length, connections[user])
        data = [d.decode() for d in data.split(b'\0')]
        if len(data) != 3:
            print('Message is not correct')
            _close_user_connection(user)
            return False
        return data_header, data

    threading.Thread(target=_connect_users).start()

    while True:
        pass


if __name__ == '__main__':
    main()
