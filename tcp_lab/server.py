# Server lab 1
import socket
import threading
import sys

HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 5001
sockets = []
clients = {}


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((IP, PORT))
    server.listen(5)
    print("Start listenning")
    sockets.append(server)
    while True:
        try:
            cli_sock, cli_addr = server.accept()
            nickname = receive_msg(cli_sock)

            if nickname:
                sockets.append(cli_sock)
                clients[cli_sock] = nickname
                print(f"New client has connected")
                code_n = f'{"+1":<{HEADER_LENGTH}}'.encode('utf-8')
                notice = f"{nickname['data'].decode('utf-8')} has join the chat".encode('utf-8')
                notice_header = f"{len(notice):<{HEADER_LENGTH}}".encode('utf-8')
                for client in clients:
                    if client != cli_sock:
                        client.send(code_n + notice_header + notice)
                handler_thread = threading.Thread(target=handler_client, args=(cli_sock, nickname, ))
                handler_thread.start()
        except KeyboardInterrupt:
            handler_thread.join()
            server.shutdown(socket.SHUT_WR)
            server.close()
            sys.exit()

def accept_connection(server):
    while True:
        cli_sock, cli_addr = server.accept()
        nickname = receive_msg(cli_sock)

        if nickname:
            sockets.append(cli_sock)
            clients[cli_sock] = nickname
            print(f"New client has connected")
            code_n = f'{"+1":<{HEADER_LENGTH}}'.encode('utf-8')
            notice = f"{nickname['data'].decode('utf-8')} has join the chat".encode('utf-8')
            notice_header = f"{len(notice):<{HEADER_LENGTH}}".encode('utf-8')
            for client in clients:
                if client != cli_sock:
                    client.send(code_n + notice_header + notice)
            handler_thread = threading.Thread(target=handler_client, args=(cli_sock, nickname, ))
            handler_thread.start()
    
def receive_msg(cli_sock):
    try:
        msg_header = cli_sock.recv(HEADER_LENGTH)

        if not len(msg_header):
            return False

        msg_length = int(msg_header.decode('utf-8').strip())

        return {'header': msg_header, 'data': cli_sock.recv(msg_length)}

    except:
        return False

def handler_client(cli_sock, nickname):
    while True:
        msg = receive_msg(cli_sock)
        if msg is False:
            cli_sock.shutdown(socket.SHUT_WR)
            cli_sock.close()
            sockets.remove(cli_sock)
            del clients[cli_sock]
            note = f"{nickname['data'].decode('utf-8')} has disconnected"
            print(note)
            return None

        print(f'Received message from {nickname["data"].decode("utf-8")}: {msg["data"].decode("utf-8")}')

        for client in clients:
            if (client != cli_sock):
                client.send(nickname['header'] + nickname['data'] + msg['header'] + msg['data'])


if __name__ == '__main__':
    main()
