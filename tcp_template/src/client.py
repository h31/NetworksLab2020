import socket
import time
import datetime
from threading import Thread

server_shutdown = False
nickname = ''


def receive_message(receive_socket: socket):
    global server_shutdown
    length = confirmation_of_message(receive_socket, 16)
    if length == '':
        server_shutdown = True
        return ''
    message = confirmation_of_message(receive_socket, int(length))
    return message


def confirmation_of_message(receive_socket: socket, length: int):
    recd = 0
    chunks = []
    try:
        while recd < length:
            chunk = receive_socket.recv(length)
            if chunk == b'':
                break
            chunks.append(chunk)
            recd += len(chunk)
    except OSError:
        print('Сервер завершил соединение')
    result = b''.join(chunks).decode('utf-8')
    return result


def convert_to_sixteen_bytes(message):
    return '{:016d}'.format(len(message))


def convert_time(time_from_server):
    timezone = -time.timezone//3600
    norm_utc_time = datetime.datetime.strptime(time_from_server, '%H:%M:%S')
    local_time = norm_utc_time + datetime.timedelta(hours=timezone)
    format_time = datetime.datetime.strftime(local_time, '%H:%M:%S')
    return format_time


class ReceiveMessageThread(Thread):
    def __init__(self, server_socket):
        Thread.__init__(self)
        self.socket = server_socket

    def run(self):
        global server_shutdown
        while not server_shutdown:
            time_server = receive_message(self.socket)
            if time_server == '':
                continue
            name_from = receive_message(self.socket)
            message = receive_message(self.socket)
            local_time = convert_time(time_server)
            print(local_time + '[' + name_from + ']:' + message)


def main():
    global nickname
    global server_shutdown
    print('Клиент запущен')
    nickname = input('Введите ваше имя ').encode('utf-8')
    try:
        sock = socket.socket()
        sock.connect(('51.15.130.137', 5004))
        length = convert_to_sixteen_bytes(nickname).encode('utf-8')
        sock.send(length)
        sock.send(nickname)
    except OSError:
        print('Не удалось подключиться к серверу')
    else:
        receive_message_thread = ReceiveMessageThread(sock)
        receive_message_thread.start()
        while True:
            message = input().encode('utf-8')
            length = convert_to_sixteen_bytes(message).encode('utf-8')
            time_message = str(datetime.datetime.utcnow().strftime('%H:%M:%S')).encode('utf-8')
            length_time_message = convert_to_sixteen_bytes(time_message).encode('utf-8')
            try:
                sock.send(length_time_message)
                sock.send(time_message)
                sock.send(length)
                sock.send(message)
            except OSError:
                print('Сервер закрыл соединение')
                break
            if message == 'exit()':
                server_shutdown = True
                break
        sock.shutdown(socket.SHUT_WR)
        sock.close()
        print('Клиент закрыт')


if __name__ == '__main__':
    main()
