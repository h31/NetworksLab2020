import socket
from threading import Thread

messages = []
clients = {}
threads = {}
end_sending = False


def receive_message(receive_socket: socket):
    length = confirmation_of_message(receive_socket, 16)
    if length == '':
        return ''
    message = confirmation_of_message(receive_socket, int(length))
    return message


def confirmation_of_message(receive_socket: socket, length: int):
    recd = 0
    chunks = []
    while recd < length:
        chunk = receive_socket.recv(length)
        if chunk == b'':
            break
        chunks.append(chunk)
        recd += len(chunk)
    result = b''.join(chunks).decode('utf-8')
    return result


def convert_to_sixteen_bytes(message):
    return '{:016d}'.format(len(message))


def add_to_messages(time: str, message: str, addr):
    global messages
    messages.append({'address': addr, 'message': message, 'time': time})


def add_to_clients(client_address, client_socket: socket, name: str):
    global clients
    clients[client_address] = (client_socket, name)


def send_message():
    global messages
    global clients
    if messages:
        address_from = messages[0]['address']
        time_message = messages[0]['time'].encode('utf-8')
        length_time_message = convert_to_sixteen_bytes(time_message).encode('utf-8')
        msg = messages.pop(0)['message'].encode('utf-8')
        length_msg = convert_to_sixteen_bytes(msg).encode('utf-8')
        name = clients[address_from][1].encode('utf-8')
        length_name = convert_to_sixteen_bytes(name).encode('utf-8')
        for client in clients.keys():
            if client != address_from:
                clients[client][0].send(length_time_message)
                clients[client][0].send(time_message)
                clients[client][0].send(length_name)
                clients[client][0].send(name)
                clients[client][0].send(length_msg)
                clients[client][0].send(msg)


def delete_client(client_address, client_socket: socket):
    del clients[client_address]
    del threads[client_address]
    client_socket.close()
    print('Отключен:', client_address)


class ReceiveThread(Thread):
    def __init__(self, client_socket: socket, client_address):
        Thread.__init__(self)
        self.socket = client_socket
        self.client_address = client_address

    def run(self):
        while True:
            if end_sending:
                break
            try:
                time_message = receive_message(self.socket)
                message = receive_message(self.socket)
            except OSError:
                print('Разорвано соединение с клиентом', self.client_address)
                break
            else:
                print(message)
                if message == 'exit()' or end_sending:
                    break
                add_to_messages(time_message, message, self.client_address)
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
        self.socket = server_socket

    def run(self):
        global end_sending
        global threads
        while True:
            if end_sending:
                break
            try:
                conn, addr = self.socket.accept()
                print('Подключен:', addr)
                name = receive_message(conn)
            except OSError:
                print('Нет возможности принять новое подключение')
            else:
                add_to_clients(addr, conn, name)
                rt = ReceiveThread(conn, addr)
                threads[addr] = rt
                rt.start()


def main():
    print('Сервер запущен')
    global end_sending
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
            end_sending = True
            for receive_thread in threads.keys():
                threads[receive_thread].socket.shutdown(socket.SHUT_WR)
                threads[receive_thread].socket.close()
            try:
                sock.shutdown(socket.SHUT_WR)
            except OSError:
                print('Сокет закрыт')
            break
    sock.close()
    print('Сервер закрыт')


if __name__ == '__main__':
    main()
