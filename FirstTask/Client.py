from datetime import datetime
import logging
import pickle
import pytz
import socket
import threading

HOST = '127.0.0.1'
PORT = 8080
HEADER_LENGTH = 10

UTC = pytz.utc


def main():
    user_name = input('Please pick a username:')

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((HOST, PORT))

    def _receive_msg():
        while True:
            try:
                data_header = server_socket.recv(HEADER_LENGTH)
                if not data_header:
                    print('No more data from the server')
                    server_socket.close()  # shutdown write, get 0 on the server, close socket on the server, then close this connection
                    return False
                data_length = int(data_header.decode('utf-8').strip())
                data = pickle.loads(server_socket.recv(data_length))
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
                msg = _build_msg(input())
                server_socket.send(msg)
            except EOFError as ex:
                logging.error(ex)
                server_socket.close()
                return False

    def _build_msg(input_msg):
        msg = {'name': user_name, 'time_sent': datetime.now(UTC), 'content': input_msg}
        msg = pickle.dumps(msg)
        msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", 'utf-8') + msg
        return msg

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
