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
            if message == 'exit()' or end_sending:
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
        # hello = 'Добро пожаловать в чат!'
        # length_hello = str(len(hello)).encode('utf-8')
        # hello_encode = hello.encode('utf-8')
        while True:
            try:
                conn, addr = self.server_socket.accept()
                print('Подключен:', addr)
                # conn.send(length_hello)
                # conn.send(hello_encode)
                # length = conn.recv(8).decode('utf-8')  # длина
                name = conn.recv(2048).decode('utf-8')
                add_to_clients(addr, conn, name)
                rt = ReceiveThread(conn, addr)
                rt.start()
            except OSError:
                print('Нет возможности принять новое подключение')
            finally:
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
        command = input()
        if command == 'exit':
            try:
                sock.shutdown(socket.SHUT_WR)
            except OSError:
                print('Были подключенные клиенты/запрос на прием или отправку данных')
            finally:
                break
    global end_sending
    end_sending = True
    sock.close()
    print('Close server')


if __name__ == '__main__':
    main()
