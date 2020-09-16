import socket


def connect():
    port = 5001
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(('', port))
    serversocket.listen(5)
    (clientsocket, address) = serversocket.accept()
    while True:
        data = clientsocket.recv(1024).decode('utf-8')
        if data == b'':
            break
        clientsocket.send("Получил".encode('utf-8'))
        print(data)
    clientsocket.close()


if __name__ == '__main__':
    connect()
