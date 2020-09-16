import socket


def connect():
    port = 5001
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', port))
    s.send("Hello cat".encode('utf-8'))
    data = s.recv(1024).decode('utf-8')
    print(data)
    s.close()


if __name__ == '__main__':
    connect()
