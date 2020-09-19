import socket
import threading

all_sock = {}
data = ""
socket_from = socket


def sending_to_all(msg, sock):
    global all_sock
    for a in all_sock.keys():
        if all_sock[a] != sock:
            all_sock[a].send(msg)


class ThreadReceive(threading.Thread):
    def __init__(self, client_address, client_socket):
        threading.Thread.__init__(self)
        self.csocket = client_socket

    def run(self):
        global all_sock
        all_sock[client_address] = clientsock
        global data
        global socket_from
        self.csocket.send("Hello from Letta".encode('UTF-8'))
        while True:
            data = self.csocket.recv(1024).decode('utf-8')
            socket_from = self.csocket
            if data == b'':
                break
            print("from client", data)
            print("address", socket_from)
        # print("Client at ", client_address, "disconnected...")


class ThreadSend(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            global data
            global socket_from
            if data != '':
                sending_to_all(bytes(data, 'UTF-8'), socket_from)
                data = ""



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
        clientsock, client_address = server.accept()
        thread_receive = ThreadReceive(client_address, clientsock)
        thread_receive.start()

