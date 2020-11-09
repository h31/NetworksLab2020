import socket
import select

clients = {}


def receive_name(sock):
    client_login = sock.recv(2048).decode('UTF-8')
    clients[sock]['name'] = client_login
    clients[sock]['mode'] = 'length_mode'


def receive_time(sock):
    msg_time = sock.recv(8).decode('UTF-8')
    clients[sock]['time'].append(msg_time)
    clients[sock]['mode'] = 'message_mode'


def receive_length(sock):
    msg_length = int(sock.recv(8).decode('UTF-8'))
    clients[sock]['length'].append(msg_length)
    clients[sock]['mode'] = 'time_mode'


def receive_msg(sock):
        chunks = []
        bytes_recd = 0
        msg_length = clients[sock]['length'][0]
        while bytes_recd < msg_length:
            chunk = sock.recv(msg_length)
            if chunk == b'':
                return False
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        data = b''.join(chunks).decode('UTF-8')
        clients[sock]['message'].append(data)
        clients[sock]['mode'] = 'send_mode'


def main():
    sockets_list = []
    localhost = "127.0.0.1"
    port = 5001
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((localhost, port))
    server.setblocking(False)
    server.listen()
    sockets_list.append(server)
    print("Server started")
    while True:
        r, w, e = select.select(sockets_list, [], [])
        for sock in r:
            if sock == server:
                client_sock, client_address = server.accept()
                client_sock.setblocking(False)
                clients[client_sock] = {'name': None, 'message': [], 'time': [], 'length': [], 'mode': 'name_mode'}
                sockets_list.append(client_sock)
            else:
                if clients[sock]['mode'] == 'name_mode':
                    receive_name(sock)
                elif clients[sock]['mode'] == 'length_mode':
                    receive_length(sock)
                elif clients[sock]['mode'] == 'time_mode':
                    receive_time(sock)
                elif clients[sock]['mode'] == 'message_mode':
                    receive_msg(sock)
                if clients[sock]['mode'] == 'send_mode':
                    msg = bytes(clients[sock]['message'][0], 'UTF-8')
                    length_msg = bytes(str(clients[sock]['length'][0]), 'UTF-8')
                    time = bytes(clients[sock]['time'][0], 'UTF-8')
                    name = bytes(clients[sock]['name'], 'UTF-8')
                    length_name = bytes(str('{:08d}'.format(len(name))), 'UTF-8')
                    for c in clients.keys():
                        if c != sock:
                            c.send(length_msg)
                            c.send(time)
                            c.send(msg)
                            c.send(length_name)
                            c.send(name)
                    clients[sock]['message'].pop(0)
                    clients[sock]['time'].pop(0)
                    clients[sock]['length'].pop(0)
                    clients[sock]['mode'] = 'length_mode'


if __name__ == '__main__':
    main()
