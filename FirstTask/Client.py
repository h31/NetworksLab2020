import socket
import threading
import os

HOST = '127.0.0.1'
PORT = 8080
HEADER_LENGTH = 10

os.system('')


def main():
    user_name = input('\033[2;32;40mPlease pick a username:\033[0m ')

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((HOST, PORT))

    def _receive_msg():
        while True:
            data_header = server_socket.recv(HEADER_LENGTH)
            data_length = int(data_header.decode('utf-8').strip())
            data = server_socket.recv(data_length).decode('utf-8')
            print(data)

    def _send_msg():
        while True:
            msg = f'{user_name}: {input()}'.encode('utf-8')
            msg_header = f"{len(msg):<{HEADER_LENGTH}}".encode('utf-8')
            server_socket.send(msg_header + msg)

    threading.Thread(target=_receive_msg).start()
    threading.Thread(target=_send_msg).start()

    while True:
        pass


if __name__ == "__main__":
    main()
