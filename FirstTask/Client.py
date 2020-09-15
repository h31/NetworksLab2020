import logging
import socket
import threading

HOST = '127.0.0.1'
PORT = 8080
HEADER_LENGTH = 10


def main():
    user_name = input('Please pick a username:')

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((HOST, PORT))

    def _receive_msg():
        while True:
            try:
                data_header = server_socket.recv(HEADER_LENGTH)
                if not len(data_header):
                    print('No more data from the server')
                    server_socket.close()
                    return False
                data_length = int(data_header.decode('utf-8').strip())
                data = server_socket.recv(data_length).decode('utf-8')
                print(data)
            except ConnectionResetError as ex:
                logging.error(ex)
                server_socket.close()
                return False
            except Exception as ex:
                logging.error(ex)
                server_socket.close()
                return False

    def _send_msg():
        while True:
            try:
                msg = f'{user_name}: {input()}'.encode('utf-8')
                msg_header = f"{len(msg):<{HEADER_LENGTH}}".encode('utf-8')
                server_socket.send(msg_header + msg)
            except EOFError as ex:
                logging.error(ex)
                server_socket.close()
                return False

    threading.Thread(target=_receive_msg).start()
    threading.Thread(target=_send_msg).start()

    while True:
        try:
            pass
        except KeyboardInterrupt as e:
            logging.error(e)
            server_socket.close()
            return False


if __name__ == "__main__":
    main()
