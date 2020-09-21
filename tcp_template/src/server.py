import socket
from threading import Thread

messages = []
clients = {}
end_sending = False


def add_to_messages(msg: str, addr):
    global messages
    messages.append((msg, addr))


def add_to_clients(client_address, client_socket: socket, name: str):
    global clients
    clients[client_address] = (client_socket, name)


def send_message():
    global messages
    global clients
    if messages:
        address_from = messages[0][1]
        msg = (clients[address_from][1] + messages.pop(0)[0]).encode('utf-8')
        for client in clients.keys():
            if client != address_from:
                clients[client][0].send(msg)


def delete_client(client_address, client_socket: socket):
    global end_sending
    del clients[client_address]
    client_socket.close()
    print('Отключен:', client_address)
    if not clients:
        end_sending = True


class ReceiveThread(Thread):
    def __init__(self, client_socket: socket, client_address):
        Thread.__init__(self)
        self.socket = client_socket
        self.client_address = client_address

    def run(self):
        while True:
            data = self.socket.recv(2048)
            if data == b'':
                break
            message = data.decode('utf-8')
            print(message)
            if message == 'exit()':
                break
            add_to_messages(message, self.client_address)
        delete_client(self.client_address, self.socket)


class SendThread(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global end_sending
        while True:
            if end_sending:
                break
            send_message()


class AcceptThread(Thread):
    def __init__(self, server_socket: socket):
        Thread.__init__(self)
        self.server_socket = server_socket

    def run(self):
        while True:
            conn, addr = self.server_socket.accept()
            print('Подключен:', addr)
            name = conn.recv(2048).decode('utf-8')
            add_to_clients(addr, conn, name)
            rt = ReceiveThread(conn, addr)
            rt.start()
            if end_sending:
                break


def main():
    print('Start server')
    sock = socket.socket()
    sock.bind(('', 5001))
    sock.listen(5)
    accept_thread = AcceptThread(sock)
    accept_thread.start()
    sending_message_thread = SendThread()
    sending_message_thread.start()
    while True:
        if end_sending:
            break
    sock.close()
    print('Close server')


if __name__ == '__main__':
    main()
