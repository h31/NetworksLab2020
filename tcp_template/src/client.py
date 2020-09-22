import socket
from threading import Thread

server_shutdown = False
nickname = ''


def receive_message(receive_socket: socket):
    global server_shutdown
    length = int(receive_socket.recv(16).decode('utf-8'))
    recd = 0
    chunks = []
    while recd < length:
        chunk = receive_socket.recv(length)
        if chunk == b'':
            server_shutdown = True
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


class ReceiveMessageThread(Thread):
    def __init__(self, server_socket):
        Thread.__init__(self)
        self.socket = server_socket

    def run(self):
        global server_shutdown
        while not server_shutdown:
            try:
                chunks = receive_message(self.socket)
            except OSError:
                print('Клиент закрыт')
                server_shutdown = True
                break
            else:
                message = b''.join(chunks).decode('utf-8')
                print(message)


def main():
    global nickname
    global server_shutdown
    print('Start client')
    nickname = '[' + input('Введите ваше имя ') + ']:'
    try:
        sock = socket.socket()
        sock.connect(('localhost', 5001))
        length = convert_to_sixteen_bytes(nickname)
        sock.send(length.encode('utf-8'))
        sock.send(nickname.encode('utf-8'))
    except OSError:
        print('Не удалось подключиться к серверу')
    else:
        receive_message_thread = ReceiveMessageThread(sock)
        receive_message_thread.start()
        while True:
            message = input()
            length = convert_to_sixteen_bytes(message)
            if message == 'exit()':
                server_shutdown = True
                break
            try:
                sock.send(length.encode('utf-8'))
                sock.send(message.encode('utf-8'))
            except OSError:
                print('Сервер закрыл соединение')
                break
        sock.shutdown(socket.SHUT_WR)
        sock.close()
        print('Close client')


if __name__ == '__main__':
    main()
