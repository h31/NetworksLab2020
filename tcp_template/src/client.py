import socket
from threading import Thread


server_shutdown = False
nickname = ''


class ReceiveMessageThread(Thread):
    def __init__(self, server_socket):
        Thread.__init__(self)
        self.socket = server_socket

    def run(self):
        global server_shutdown
        while not server_shutdown:
            try:
                data = self.socket.recv(2048)
                if data == b'':
                    server_shutdown = True
                    break
                message = data.decode('utf-8')
                print(message)
            except OSError:
                print('Клиент закрыт')
                server_shutdown = True
                break



def main():
    global nickname
    global server_shutdown
    print('Start client')
    nickname = '[' + input('Введите ваше имя ') + ']:'
    sock = socket.socket()
    sock.connect(('localhost', 5001))
    sock.send(nickname.encode('utf-8'))
    receive_message_thread = ReceiveMessageThread(sock)
    receive_message_thread.start()
    while True:
        message = input()
        if message == 'exit()':
            server_shutdown = True
            break
        try:
            sock.send(message.encode('utf-8'))
        except OSError:
            print('Сервер закрыл соединение')
            break
    sock.shutdown(socket.SHUT_WR)
    sock.close()
    print('Close client')


if __name__ == '__main__':
    main()
