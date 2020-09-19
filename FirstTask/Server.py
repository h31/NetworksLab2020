import logging
import pickle
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
                data_header, data = _receive_data(user)

                if not data_header or not data or connecting:
                    print('No more data from the client')
                    connections[user].close()
                    break

                for each in range(len(connections)):
                    connections[each].send(data_header + pickle.dumps(data))
            except ConnectionResetError as ex:
                logging.error(ex)
                connections[user].close()
                print(f'user n.{user + 1} has been disconnected')
                connections.remove(connections[user])
                return False

    def _receive_data(user):
        data_header = server_socket.receive_bytes_num(HEADER_LENGTH, connections[user])
        if not data_header:
            return False, False
        data_length = int(data_header.decode('utf-8').strip())
        data = pickle.loads(server_socket.receive_bytes_num(data_length, connections[user]))
        return data_header, data

    threading.Thread(target=_connect_users).start()

    while True:
        pass


if __name__ == '__main__':
    main()
