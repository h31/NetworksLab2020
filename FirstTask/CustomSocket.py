import socket


class CustomSocket:
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def setsockopt(self):
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def bind(self, host, port):
        self.sock.bind((host, port))

    def listen(self, connections_num):
        self.sock.listen(connections_num)

    def accept(self):
        return self.sock.accept()

    def connect(self, host, port):
        self.sock.connect((host, port))

    def close(self):
        self.sock.close()

    def shutdown(self):
        self.sock.shutdown(socket.SHUT_WR)

    def send(self, num):
        self.sock.send(num)

    def send_all(self, data, current_socket=None):
        if current_socket is None:
            current_socket = self.sock
        current_socket.sendall(bytes(data, encoding='utf-8'))


    '''def recv(self, num):
        self.sock.recv(num)'''

    def is_closed(self):
        return True if self.sock.fileno() == -1 else False

    def send_bytes_num(self, msg, msg_len):
        total_sent = 0
        while total_sent < msg_len:
            sent = self.sock.send(msg[total_sent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            total_sent = total_sent + sent

    def receive_bytes_num(self, number, current_socket=None):
        if current_socket is None:
            current_socket = self.sock
        chunks = []
        bytes_received = 0
        while bytes_received < number:
            chunk = current_socket.recv(number - bytes_received)
            if chunk == b'':
                return False
            chunks.append(chunk)
            bytes_received = bytes_received + len(chunk)
        return b''.join(chunks)

    def receive(self, current_socket=None):
        if current_socket is None:
            current_socket = self.sock
        return current_socket.recv(4096)
