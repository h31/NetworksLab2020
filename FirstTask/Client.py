from datetime import datetime, timedelta, timezone
import logging
import pickle
import pytz
import threading
from termcolor import colored

from FirstTask.CustomSocket import CustomSocket
from FirstTask.MessageValidator import MessageValidator

HOST = '127.0.0.1'
PORT = 8080
HEADER_LENGTH = 10

UTC = pytz.utc
local_timezone = datetime.now(timezone.utc).astimezone()
utc_offset = local_timezone.utcoffset() // timedelta(seconds=1)

message_validator = MessageValidator()


def main():
    user_name = input('Please pick a username:')

    server_socket = CustomSocket()
    server_socket.connect(HOST, PORT)

    def _receive_msg():
        while True:
            try:
                data_header = server_socket.receive_bytes_num(HEADER_LENGTH)
                if not data_header:
                    print('No more data from the server')
                    server_socket.close()  # shutdown write, get 0 on the server, close socket on the server, then close this connection
                    return False
                data_length = int(data_header.decode('utf-8').strip())
                data = pickle.loads(server_socket.receive_bytes_num(data_length))
                _print_msg(data)
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
                msg, msg_len = _build_msg(input())
                server_socket.send_bytes_num(msg, msg_len)
            except EOFError as ex:
                logging.error(ex)
                server_socket.close()
                return False

    def _build_msg(input_msg):
        while not input_msg:
            input_msg = input()
        msg = {'name': user_name, 'time_sent': datetime.now(UTC), 'content': input_msg}
        msg = pickle.dumps(msg)
        msg_len = len(msg)
        msg = bytes(f"{msg_len:<{HEADER_LENGTH}}", 'utf-8') + msg
        return msg, msg_len

    def _print_msg(msg):
        if not message_validator.check(msg):
            print('Message is not correct')
            server_socket.close()  # shutdown write, get 0 on the server, close socket on the server, then close this connection
            return False
        msg_user_name = msg['name']
        msg_time_sent = (msg['time_sent'] + timedelta(0, utc_offset)).strftime('%H:%M')
        msg_content = msg['content']
        user_name_color = 'magenta' if (msg_user_name != user_name) else 'yellow'
        print(colored(msg_user_name, user_name_color, attrs=['bold']),
              colored(msg_time_sent, 'blue'),
              colored(msg_content, 'cyan'))

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
