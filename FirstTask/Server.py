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
            connections.append(conn)
            connecting = True
            print(addr, 'connected')
            for each in range(len(connections)):
                threading.Thread(target=_send_data, args=(each,)).start()
            connecting = False
            threading.Thread(target=_connect_users).start()

    def _send_data(user):
        while True:
            data_header = connections[user].recv(HEADER_LENGTH)
            data_length = int(data_header.decode('utf-8').strip())
            data = connections[user].recv(data_length).decode('utf-8')
            for each in range(len(connections)):
                connections[each].send(data_header + data.encode('utf-8'))
            if not data or connecting:
                break
        print('Closing connections')
        server_socket.close()

    threading.Thread(target=_connect_users).start()

    while True:
        pass


if __name__ == '__main__':
    main()
