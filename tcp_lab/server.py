# Server lab 2
import socket
from datetime import datetime
import os
import select

HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 5002
clients = {}
sockets = []


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(False)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((IP, PORT))
    server.listen(5)
    sockets.append(server)
    print("Start listenning")

    try:
        while True:
            readable_sock, writable_sock, exception_sock = select.select(
                sockets, [], [])
            for sock_fd in readable_sock:
                if sock_fd == server:
                    cli_sock, cli_addr = server.accept()
                    cli_sock.setblocking(False)
                    sockets.append(cli_sock)
                    current_time = datetime.now().strftime("%H:%M")
                    nickname = receive_msg(cli_sock)
                    if nickname:
                        clients[cli_sock] = nickname
                        print(f"At {current_time} New client has connected")
                        notify('+1', cli_sock)
                    else:
                        continue
                else:
                    hander = handler_client(sock_fd)
                    if hander is False:
                        continue

    except KeyboardInterrupt:
        for cl in clients:
            cl.shutdown(socket.SHUT_WR)
            cl.close()
        server.shutdown(socket.SHUT_WR)
        server.close()
        os._exit(0)


def broadcast(msg, cli_sock):
    for client in clients:
        if client != cli_sock:
            client.send(msg)


def notify(typeOfn, cli_sock):
    code_n = f'{typeOfn:<{HEADER_LENGTH}}'.encode('utf-8')
    nickname = clients[cli_sock]
    notice = ""
    if (typeOfn == '+1'):
        notice = f"{nickname['data'].decode('utf-8')} has join the chat".encode(
            'utf-8')
    if (typeOfn == '-1'):
        notice = f"{nickname['data'].decode('utf-8')} has out from the chat".encode(
            'utf-8')
    notice_header = f"{len(notice):<{HEADER_LENGTH}}".encode('utf-8')
    msg = code_n + notice_header + notice
    broadcast(msg, cli_sock)


def receive_msg(cli_sock):
    try:
        msg_header = cli_sock.recv(HEADER_LENGTH)

        if not len(msg_header):
            return False

        msg_length = int(msg_header.decode('utf-8').strip())

        msg = cli_sock.recv(msg_length)

        return {'header': msg_header, 'data': msg}

    except ValueError:
        print("Type of header must be 'int'")
        return False
    
    except:
        return False


def handler_client(cli_sock):
    msg = receive_msg(cli_sock)
    nickname = clients[cli_sock]
    if msg is False:
        cli_sock.shutdown(socket.SHUT_WR)
        cli_sock.close()
        sockets.remove(cli_sock)
        note = f"{nickname['data'].decode('utf-8')} has disconnected"
        print(note)
        notify('-1', cli_sock)
        del clients[cli_sock]
        return None

    send_time = receive_msg(cli_sock)

    current_time = datetime.now().strftime("%H:%M")

    print(
        f'At {current_time} received message from {nickname["data"].decode("utf-8")}: {msg["data"].decode("utf-8")}')

    full_msg = nickname['header'] + nickname['data'] + msg['header'] + msg['data'] + send_time['header'] + send_time['data']
    broadcast(full_msg, cli_sock)


if __name__ == '__main__':
    main()