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
    del clients[client_address]
    client_socket.shutdown(socket.SHUT_RD)
    client_socket.close()


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


def main():
    print('Start server')
    server_socket = socket.socket()
    server_socket.bind(('', 5001))
    server_socket.listen(5)
    sending_message_thread = SendingMessageThread()
    sending_message_thread.run()
    while True:
        conn, addr = server_socket.accept()
        add_to_clients(addr, conn)
        rt = ClientThread(conn, addr)
        rt.run()


if __name__ == '__main__':
    main()
