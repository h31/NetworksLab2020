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
            data = self.socket.recv(2048)
            if data == b'':
                server_shutdown = True
                break
            message = data.decode('utf-8')
            print(message)


def main():
    global nickname
    global server_shutdown
    print('Start client')
    nickname = '[' + input('Введите ваше имя ') + ']:'
    sock = socket.socket()
    sock.connect(('localhost', 5001))
    receive_message_thread = ReceiveMessageThread(sock)
    receive_message_thread.start()
    while not server_shutdown:
        message = input()
        sock.send((nickname + message).encode('utf-8'))
        if message == 'exit()':
            server_shutdown = True
            break
    sock.shutdown(socket.SHUT_WR)
    sock.close()
    print('Close client')


if __name__ == '__main__':
    main()
