import socket
from threading import Thread


server_shutdown = False
nickname = ''


class ReceiveMessageThread(Thread):
    def __init__(self, server_socket):
        Thread.__init__(self)
        self.socket = server_socket

    def run(self):
        while True:
            data = self.socket.recv(2048)
            if data == b'':
                break
            message = data.decode('utf-8')
            print(message)


def main():
    global nickname
    print('Start client')
    nickname = '[' + input('Введите ваше имя ') + ']:'
    sock = socket.socket()
    sock.connect(('localhost', 5001))
    receive_message_thread = ReceiveMessageThread(sock)
    receive_message_thread.start()
    while True:
        if server_shutdown:
            break
        message = input()
        sock.send((nickname + message).encode('utf-8'))
    sock.shutdown(socket.SHUT_RD)
    sock.close()
    print('Close client')


if __name__ == '__main__':
    main()
