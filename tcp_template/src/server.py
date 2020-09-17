import socket
from threading import Thread

messages = []
clients = {}
end_sending = False


def add_to_messages(msg: str):
    global messages
    messages.append(msg)


def add_to_clients(client_address, client_socket: socket):
    global clients
    clients[client_address] = client_socket


def send_message():
    global messages
    global clients
    if messages:
        msg = messages.pop(0).encode('utf-8')
        for client in clients.keys():
            clients[client].send(msg)


def delete_client(client_address, client_socket: socket):
    global end_sending
    del clients[client_address]
    client_socket.close()
    print('Отключен:', client_address)
    if not clients:
        end_sending = True


class ClientThread(Thread):
    def __init__(self, client_socket: socket, client_address):
        Thread.__init__(self)
        self.socket = client_socket
        self.client_address = client_address

    def run(self):
        print('Подключен:', self.client_address)
        self.socket.send('Добро пожаловать в чат!'.encode('utf-8'))
        while True:
            data = self.socket.recv(2048)
            if data == b'':
                break
            message = data.decode('utf-8')
            name = message.find(':') + 1
            if message[name:] == 'exit()':
                break
            add_to_messages(message)
        delete_client(self.client_address, self.socket)


class SendingMessageThread(Thread):
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
            add_to_clients(addr, conn)
            rt = ClientThread(conn, addr)
            rt.start()
            if end_sending:
                break


def main():
    print('Start server')
    sock = socket.socket()
    sock.bind(('', 5001))
    sock.listen(5)
    sending_message_thread = SendingMessageThread()
    sending_message_thread.start()
    accept_thread = AcceptThread(sock)
    accept_thread.start()
    while True:
        if end_sending:
            break
    sock.close()
    print('Close server')


if __name__ == '__main__':
    main()
