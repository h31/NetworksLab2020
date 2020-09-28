import socket
import threading

all_sock = {}
data = ""
socket_from = socket
client_login = ""
names = {}
length = 0
length_length = 8


def to_bytes(text):
    text_bytes = bytes(text, 'UTF-8')
    return text_bytes


def sending_to_all(msg, sock):
    global all_sock
    global names
    global socket_from
    for a in all_sock.keys():
        if all_sock[a] != sock:
            login_bytes = to_bytes("[" + names[socket_from] + "]" + ":")
            all_sock[a].send(login_bytes + msg)
    return len(login_bytes+msg)


def sending_to_all_without_name(msg, sock):
    global all_sock
    global socket_from
    for a in all_sock.keys():
        if all_sock[a] != sock:
            all_sock[a].send(msg)


class ThreadReceive(threading.Thread):
    def __init__(self, client_address, client_socket):
        threading.Thread.__init__(self)
        self.csocket = client_socket
        self.cadrress = client_address

    def run(self):
        global all_sock
        all_sock[self.cadrress] = self.csocket
        global data
        global length
        global socket_from
        global client_login
        global names
        client_login = self.csocket.recv(2048).decode('UTF-8')
        names[self.csocket] = client_login
        while True:
            length = int(self.csocket.recv(length_length).decode('UTF-8'))
            print(length)
            socket_from = self.csocket
            chunks = []
            bytes_recd = 0
            while bytes_recd < length:
                chunk = self.csocket.recv(length)
                if chunk == b'':
                    raise RuntimeError("socket connection broken")
                if chunk == "leave chat":
                    break
                chunks.append(chunk)
                bytes_recd = bytes_recd + len(chunk)
            data = b''.join(chunks)
            print("message from client", data)


class ThreadSend(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global length
        while True:
            total_sent = 0
            global data
            global names
            global socket_from
            global client_login
            while total_sent < int(length):
                if data != '':
                    length_name_message = '{:08d}'.format((int(length)+len(names[socket_from])+3))
                    sending_to_all_without_name(to_bytes(length_name_message), socket_from)
                    sent = sending_to_all(data[total_sent:], socket_from)
                    data = ""
                    if sent == 0:
                        raise RuntimeError("socket connection broken")
                    total_sent = total_sent + sent
                    print("send length"+length_name_message)


if __name__ == '__main__':
    LOCALHOST = "127.0.0.1"
    PORT = 5001
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((LOCALHOST, PORT))
    print("Server started")
    server.listen(5)
    thread_send = ThreadSend()
    thread_send.start()
    while True:
        client_sock, client_address = server.accept()
        thread_receive = ThreadReceive(client_address, client_sock)
        thread_receive.start()
