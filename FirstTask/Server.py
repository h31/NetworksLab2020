import select
import socket
from queue import Queue

from FirstTask.CustomSocket import CustomSocket

HOST = '127.0.0.1'
PORT = 8080
HEADER_LENGTH = 10
USERS_EXPECTED_NUMBER = 10

TIMEOUT = 1000
READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR
READ_WRITE = READ_ONLY | select.POLLOUT


def main():
    server_socket = CustomSocket()
    server_socket.setsockopt()
    server_socket.bind(HOST, PORT)
    server_socket.listen(USERS_EXPECTED_NUMBER)
    print('Waiting for users...')

    poller = select.poll()
    poller.register(server_socket.get_socket(), READ_ONLY)
    fd_to_socket = {server_socket.get_socket().fileno(): server_socket.get_socket(), }
    message_queues = {}

    def _add_connection():
        conn, addr = server_socket.accept()
        print(f'User with address {addr} has connected')
        fd_to_socket[conn.fileno()] = [conn, addr]
        poller.register(conn, READ_ONLY)
        message_queues[conn] = Queue()

    def _remove_conn(sock, addr):
        poller.unregister(sock)
        del fd_to_socket[sock.fileno()]
        del message_queues[sock]
        sock.shutdown(socket.SHUT_WR)
        sock.close()
        print(f'User with address {addr} has disconnected')

    def _receive_data(user, addr):
        data_header = server_socket.receive_bytes_num(HEADER_LENGTH, user)
        if not data_header:
            return False, False
        data_length = int(data_header.decode().strip())
        data = server_socket.receive_bytes_num(data_length, user)
        data = [d.decode() for d in data.split(b'\0')]
        if len(data) != 3:
            print('Message is not correct')
            _remove_conn(user, addr)
            return False
        return data_header, data

    def _broadcast_msg():
        next_msg = message_queues[current_socket].get_nowait()
        for each in fd_to_socket.values():
            if type(each) is not list:
                continue
            data_new_msg = b'\0'.join([bytes(d, 'utf-8') for d in next_msg[1]])
            each[0].send(next_msg[0] + data_new_msg)

    while True:
        events = poller.poll(TIMEOUT)
        for fd, flag in events:
            current_socket = fd_to_socket[fd][0] if type(fd_to_socket[fd]) == list else fd_to_socket[fd]

            if flag & (select.POLLIN | select.POLLPRI):
                if current_socket is server_socket.get_socket():
                    _add_connection()
                else:
                    header, msg_data = _receive_data(current_socket, fd_to_socket[fd][1])
                    if header and msg_data:
                        message_queues[current_socket].put([header, msg_data])
                        poller.modify(current_socket, READ_WRITE)
                    else:
                        _remove_conn(current_socket, fd_to_socket[fd][1])
            elif flag & select.POLLOUT:
                if not message_queues[current_socket].empty():
                    _broadcast_msg()
                else:
                    poller.modify(current_socket, READ_ONLY)
            elif flag & select.POLLERR:
                _remove_conn(current_socket, fd_to_socket[fd][1])


if __name__ == '__main__':
    main()
