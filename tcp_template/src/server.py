import socket
import threading

all_sock = {}
data = ""
socket_from = socket
names = {}
length = 0
message_time = 0


def to_bytes(text):
    text_bytes = bytes(text, 'UTF-8')
    return text_bytes


def sending_to_all(msg, sock):
    global all_sock
    global names
    global socket_from
    global message_time
    for a in all_sock.keys():
        if all_sock[a] != sock:
            all_sock[a].send(msg)
    return len(msg)


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
        global names
        global message_time
        client_login = self.csocket.recv(2048).decode('UTF-8')
        names[self.csocket] = client_login
        while True:
            length = int(self.csocket.recv(8).decode('UTF-8'))
            message_time = self.csocket.recv(8).decode('UTF-8')
            print(message_time)
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
            global message_time
            while total_sent < int(length):
                if data != '':
                    name_length = '{:08d}'.format(len(names[socket_from]))
                    length_name_message = '{:08d}'.format((int(length)))
                    sending_to_all(to_bytes(length_name_message), socket_from)
                    sending_to_all(to_bytes(message_time), socket_from)
                    sending_to_all(to_bytes(name_length), socket_from)
                    sending_to_all(to_bytes(names[socket_from]), socket_from)
                    sent = sending_to_all(data[total_sent:], socket_from)
                    data = ""
                    if sent == 0:
                        raise RuntimeError("socket connection broken")
                    total_sent = total_sent + sent
                    print("send length"+length_name_message)


def main():
    localhost = "127.0.0.1"
    port = 5001
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((localhost, port))
    print("Server started")
    server.listen(5)
    thread_send = ThreadSend()
    thread_send.start()
    while True:
        client_sock, client_address = server.accept()
        thread_receive = ThreadReceive(client_address, client_sock)
        thread_receive.start()


if __name__ == '__main__':
    main()
