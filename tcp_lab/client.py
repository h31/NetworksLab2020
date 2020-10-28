# Client lab 1
import threading
import socket
from datetime import datetime
import time
import sys

HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 5001


def main():
    nickname_str = input("Enter your username: ")
    cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cli_sock.connect((IP, PORT))

    nickname_code = nickname_str.encode('utf-8')
    nickname_header = f"{len(nickname_code):<{HEADER_LENGTH}}".encode('utf-8')
    cli_sock.send(nickname_header + nickname_code)

    send_thread = threading.Thread(target=send_msg, args=(cli_sock, ))
    receive_thread = threading.Thread(target=receive_msg, args=(cli_sock, ))
    try:
        send_thread.start()
        receive_thread.start()

    except KeyboardInterrupt:
        cli_sock.shutdown(socket.SHUT_WR)
        cli_sock.close()
        sys.exit()
        
def send_msg(cli_sock):
    try:
        while True:
            msg = input()

            if msg:
                msg_code = msg.encode('utf-8')
                msg_header = f"{len(msg_code):<{HEADER_LENGTH}}".encode('utf-8')
                send_time = str(time.time()).encode('utf-8')
                send_time_header = f"{len(send_time):<{HEADER_LENGTH}}".encode('utf-8')

                cli_sock.send(msg_header + msg_code + send_time_header + send_time)
    except:
        cli_sock.shutdown(socket.SHUT_WR)
        cli_sock.close()
        sys.exit()


def receive_msg(cli_sock):
    while True:
        snickname_header = cli_sock.recv(HEADER_LENGTH)

        if not len(snickname_header):
            print('Connection lost')
            cli_sock.shutdown(socket.SHUT_WR)
            cli_sock.close()
            break

        if snickname_header.decode('utf-8').strip() == '+1':
            notice_length = int(cli_sock.recv(HEADER_LENGTH).decode('utf-8').strip())
            notice = cli_sock.recv(notice_length).decode('utf-8')
            print(f'{notice}')
            continue

        if snickname_header.decode('utf-8').strip() == '-1':
            notice_length = int(cli_sock.recv(HEADER_LENGTH).decode('utf-8').strip())
            notice = cli_sock.recv(notice_length).decode('utf-8')
            print(f'{notice}')
            continue

        snickname_length = int(snickname_header.decode('utf-8').strip())

        snickname = cli_sock.recv(snickname_length).decode('utf-8')

        msg_header = cli_sock.recv(HEADER_LENGTH)
        msg_length = int(msg_header.decode('utf-8').strip())
        msg = cli_sock.recv(msg_length).decode('utf-8')

        send_time_header = cli_sock.recv(HEADER_LENGTH)
        time_length = int(send_time_header.decode('utf-8').strip())
        send_time = float(cli_sock.recv(time_length).decode('utf-8'))
        str_time = datetime.fromtimestamp(send_time).strftime("%H:%M")
        
        print(f'<{str_time}> [{snickname}]: {msg}')


if __name__ == '__main__':
    main()