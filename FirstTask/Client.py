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
    connected = False

    print('Welcome to the Chat Room! For exit print "exit"')
    user_name = input('Please pick a username:')

    server_socket = CustomSocket()
    print("Connecting to server...")
    while not connected:
        try:
            server_socket.connect(HOST, PORT)
            print("Connected. You can start chatting!")
            connected = True
        except ConnectionRefusedError:
            pass

    def _receive_msg():
        while True:
            try:
                data_header = server_socket.receive_bytes_num(HEADER_LENGTH)
                if not data_header:
                    server_socket.close()
                    return False
                data_length = int(data_header.decode('utf-8').strip())
                data = pickle.loads(server_socket.receive_bytes_num(data_length))
                _print_msg(data)
            except ConnectionResetError:
                server_socket.close()
                return False
            except Exception as ex:
                logging.error(ex)
                server_socket.close()
                return False

    def _send_msg():
        while True:
            msg, msg_len = _build_msg(input())
            if threading.active_count() < 3:
                return False
            server_socket.send_bytes_num(msg, msg_len)

    def _build_msg(input_msg):
        while not input_msg:
            input_msg = input()
        if input_msg == 'exit':
            if not server_socket.is_closed():
                server_socket.shutdown()
            return False, False
        msg = {'name': user_name, 'time_sent': datetime.now(UTC), 'content': input_msg}
        msg = pickle.dumps(msg)
        msg_len = len(msg)
        msg = bytes(f"{msg_len:<{HEADER_LENGTH}}", 'utf-8') + msg
        return msg, msg_len

    def _print_msg(msg):
        if not message_validator.check(msg):
            print('Message from the server is not correct')
            server_socket.close()
            return False
        msg_user_name = msg['name']
        msg_time_sent = (msg['time_sent'] + timedelta(0, utc_offset)).strftime('%H:%M')
        msg_content = msg['content']
        user_name_color = 'magenta' if (msg_user_name != user_name) else 'yellow'
        print(colored(msg_user_name, user_name_color, attrs=['bold']),
              colored(msg_time_sent, 'blue'),
              colored(msg_content, 'cyan'))

    receive_thread = threading.Thread(target=_receive_msg)
    receive_thread.daemon = True
    receive_thread.start()
    send_thread = threading.Thread(target=_send_msg)
    send_thread.start()

    while True:
        if threading.active_count() < 3:
            if send_thread.is_alive():
                print('Closing Time. Type something to exit!')
            return False


if __name__ == "__main__":
    main()
