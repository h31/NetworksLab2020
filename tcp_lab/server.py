# Server lab 2
import socket
from datetime import datetime
import os
import select
#import errno

HEADER_LENGTH = 10

IP = "0.0.0.0"
PORT = 5008
clients_names = {}
clients_list = []
sockets = []
buffer = []


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
                sockets, [], sockets)
            for sock_fd in readable_sock:
                if sock_fd == server:
                    cli_sock, cli_addr = server.accept()
                    cli_sock.setblocking(False)
                    sockets.append(cli_sock)
                    clients_list.append(cli_sock)
                    buffer.append([0, b""])
                    current_time = datetime.now().strftime("%H:%M")
                    print(f"At {current_time} New client has connected")
                    nickname = receive(cli_sock)
                    clients_names[cli_sock] = nickname
                    notify('+1', cli_sock)
                else:
                    handler_client(sock_fd)
            for sock_fd in exception_sock:
                sockets.remove(sock_fd)
                del clients_names[sock_fd]
    

    except KeyboardInterrupt:
        for cl in clients_names:
            cl.shutdown(socket.SHUT_WR)
            cl.close()
        server.shutdown(socket.SHUT_WR)
        server.close()
        os._exit(0)

def broadcast(msg, cli_sock):
    for client in clients_list:
        if client != cli_sock:
            client.send(msg)


def notify(typeOfn, cli_sock):
    code_n = f'{typeOfn:<{HEADER_LENGTH}}'.encode('utf-8')
    nickname = clients_names[cli_sock]
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


def receive(cli_sock):
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
    ind_cli = clients_list.index(cli_sock)
    nickname = clients_names[cli_sock]
    if buffer[ind_cli][0] == 0 and buffer[ind_cli][1] == b"":
        header_msg = b""
        # try:
        header_msg = cli_sock.recv(HEADER_LENGTH)
        # except IOError as e:
        #     if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
        #         os._exit(0)
        #     return

        if not header_msg:
            cli_sock.shutdown(socket.SHUT_WR)
            cli_sock.close()
            sockets.remove(cli_sock)
            note = f"{nickname['data'].decode('utf-8')} has disconnected"
            print(note)
            notify('-1', cli_sock)
            clients_list.remove(cli_sock)
            del clients_names[cli_sock]
            return False
        msg_length = int(header_msg.decode('utf-8').strip())
        msg = cli_sock.recv(msg_length)        
        buffer[ind_cli][1] = msg
        buffer[ind_cli][0] = msg_length

    
    else:
        tmp_length = buffer[ind_cli][0] - len(buffer[ind_cli][1])
        buffer[ind_cli][1] += cli_sock.recv(tmp_length)
    
    if buffer[ind_cli][0] == len(buffer[ind_cli][1]):
        msg_code = buffer[ind_cli][1]
        msg_header = f"{buffer[ind_cli][0]:<{HEADER_LENGTH}}".encode('utf-8')
        buffer[ind_cli][0] = 0
        buffer[ind_cli][1] = b""

        send_time = receive(cli_sock)

        current_time = datetime.now().strftime("%H:%M")

        print(
            f'At {current_time} received message from {nickname["data"].decode("utf-8")}: {msg_code.decode("utf-8")}')

        # print(msg_header)
        # print(len(msg_code))
        full_msg = msg_header + msg_code + nickname['header'] + nickname['data'] + send_time['header'] + send_time['data']
        broadcast(full_msg, cli_sock)
        return


if __name__ == '__main__':
    main()