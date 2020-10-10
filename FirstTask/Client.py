from datetime import datetime, timedelta, timezone
import logging
import pytz
import select
import threading
from termcolor import colored
from queue import Queue

from FirstTask.CustomSocket import CustomSocket

HOST = '127.0.0.1'
PORT = 8080
HEADER_LENGTH = 10

TIMEOUT = 1000
READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR
READ_WRITE = READ_ONLY | select.POLLOUT

UTC = pytz.utc
local_timezone = datetime.now(timezone.utc).astimezone()
utc_offset = local_timezone.utcoffset() // timedelta(seconds=1)


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
    poller = select.poll()
    poller.register(server_socket.get_socket(), READ_WRITE)

    message_queue = Queue()

    def _close_connection():
        poller.unregister(server_socket.get_socket())
        server_socket.shutdown()
        server_socket.close()

    def _receive_msg():
        nonlocal connected
        if not connected:
            return
        try:
            data_header = server_socket.receive_bytes_num(HEADER_LENGTH)
            if not data_header:
                connected = False
                _close_connection()
                return
            data_length = int(data_header.decode().strip())
            data = server_socket.receive_bytes_num(data_length)
            _print_msg(data)
        except ConnectionResetError as ex:
            logging.error(ex)
            _close_connection()
            return False

    def _get_input_msg():
        nonlocal connected
        while connected:
            msg, msg_len = _build_msg(input())
            if not msg or not msg_len:
                connected = False
            message_queue.put([msg, msg_len])

    def _send_msg():
        next_msg = message_queue.get_nowait()
        server_socket.send_bytes_num(next_msg[0], next_msg[1])

    def _build_msg(input_msg):
        nonlocal connected
        while not input_msg:
            input_msg = input()
        if input_msg == 'exit':
            if not server_socket.is_closed():
                poller.modify(server_socket.get_socket(), READ_ONLY)
                server_socket.shutdown()
            return False, False
        msg = _encode_msg(input_msg)
        msg_len = len(msg)
        msg = bytes(f"{msg_len:<{HEADER_LENGTH}}", 'utf-8') + msg
        return msg, msg_len

    def _encode_msg(input_msg):
        _user_name = bytes(user_name, 'utf-8')
        _send_date = bytes(datetime.now(UTC).strftime('%Y/%m/%d/%H/%M'), 'utf-8')
        _input_msg = bytes(input_msg, 'utf-8')
        return b'\0'.join([_user_name, _send_date, _input_msg])

    def _decode_msg(msg):
        msg = [m.decode() for m in msg.split(b'\0')]
        try:
            msg_user_name = msg[0]
            msg_time_sent = datetime.strptime(msg[1], '%Y/%m/%d/%H/%M')
            msg_time_sent = (msg_time_sent + timedelta(0, utc_offset)).strftime('%H:%M')
            msg_content = msg[2]
            return msg_user_name, msg_time_sent, msg_content
        except ValueError or IndexError:
            print('Message from the server is not correct')
            _close_connection()
            return False

    def _print_msg(msg):
        msg_user_name, msg_time_sent, msg_content = _decode_msg(msg)
        user_name_color = 'magenta' if (msg_user_name != user_name) else 'yellow'
        print(colored(msg_user_name, user_name_color, attrs=['bold']),
              colored(msg_time_sent, 'blue'),
              colored(msg_content, 'cyan'))

    send_thread = threading.Thread(target=_get_input_msg)
    send_thread.start()

    while connected:
        events = poller.poll(TIMEOUT)

        for fd, flag in events:
            if flag & (select.POLLIN | select.POLLPRI):
                _receive_msg()
            elif flag & select.POLLOUT:
                if not message_queue.empty():
                    _send_msg()
            if flag & select.POLLERR:
                logging.error('Error occurred while polling')
                _close_connection()


if __name__ == "__main__":
    main()
