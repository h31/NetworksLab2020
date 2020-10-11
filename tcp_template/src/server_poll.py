import socket
import select

names = {}


def receive_name(sock):
    client_login = sock.recv(2048).decode('UTF-8')
    names[sock] = client_login
    return names


def receive_msg(sock):
    msg_length = int(sock.recv(8).decode('UTF-8'))
    msg_time = sock.recv(8).decode('UTF-8')
    chunks = []
    bytes_recd = 0
    while bytes_recd < msg_length:
        chunk = sock.recv(msg_length)
        if chunk == b'':
            raise RuntimeError("socket connection broken")
        if chunk == "leave chat":
            break
        chunks.append(chunk)
        bytes_recd = bytes_recd + len(chunk)
    data = b''.join(chunks)
    msg_length = '{:08d}'.format(msg_length)
    return str(msg_length)+msg_time+data.decode('UTF-8')


def main():
    sockets = []
    clients = []
    localhost = "127.0.0.1"
    port = 5001
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((localhost, port))
    print("Server started")
    server.listen(5)
    sockets.append(server)
    while True:
        r = []
        r, w, e = select.select(sockets, [], [])
        for sock in r:
            if sock == server:
                client_sock, client_address = server.accept()
                sockets.append(client_sock)
                clients.append(client_sock)
                name = receive_name(client_sock)
            else:
                message = receive_msg(sock)
                login = name[sock]
                print(login)
                for c in clients:
                    if c != sock:
                        c.send(bytes(str(message), 'UTF-8'))
                        name_length = '{:08d}'.format(len(name[sock]))
                        c.send(bytes(str(name_length), 'UTF-8'))
                        c.send(bytes(name[sock], 'UTF-8'))


if __name__ == '__main__':
    main()
