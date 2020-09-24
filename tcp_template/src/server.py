import socket
from threading import Thread

messages = []
clients = {}
end_sending = False


def receive_message(receive_socket: socket):
    length = int(receive_socket.recv(16).decode('utf-8'))
    recd = 0
    chunks = []
    while recd < length:
        chunk = receive_socket.recv(length)
        if chunk == b'':
            break
        chunks.append(chunk)
        recd += len(chunk)
    return chunks


def convert_to_sixteen_bytes(name: str):
    length_list = []
    length_name = str(len(name))
    for i in length_name:
        length_list.append(i)
    while len(length_list) < 16:
        length_list.insert(0, '0')
    return ''.join(length_list)


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
        msg = clients[address_from][1] + messages.pop(0)[0]
        length = convert_to_sixteen_bytes(msg)
        for client in clients.keys():
            if client != address_from:
                clients[client][0].send(length.encode('utf-8'))
                clients[client][0].send(msg.encode('utf-8'))


def delete_client(client_address, client_socket: socket):
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
            try:
                chunks = receive_message(self.socket)
            except OSError:
                print('Разорвано соединение с клиентом')
                break
            else:
                message = b''.join(chunks).decode('utf-8')
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
            try:
                send_message()
            except OSError:
                print('Нет возможности отправить данные клиентам')


class AcceptThread(Thread):
    def __init__(self, server_socket: socket):
        Thread.__init__(self)
        self.server_socket = server_socket

    def run(self):
        global end_sending
        while True:
            try:
                conn, addr = self.server_socket.accept()
                print('Подключен:', addr)
                chunks = receive_message(conn)
            except OSError:
                print('Нет возможности принять новое подключение')
            else:
                name = b''.join(chunks).decode('utf-8')
                add_to_clients(addr, conn, name)
                rt = ReceiveThread(conn, addr)
                rt.start()
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
