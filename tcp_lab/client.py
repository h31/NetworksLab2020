# Client lab 1
import threading
import socket
from datetime import datetime
import sys

HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 5001


def main():
    try:
        nickname_str = input("Enter your username: ")
        cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cli_sock.connect((IP, PORT))

        nickname_code = nickname_str.encode('utf-8')
        nickname_header = f"{len(nickname_code):<{HEADER_LENGTH}}".encode('utf-8')
        cli_sock.send(nickname_header + nickname_code)

        send_thread = threading.Thread(target=send_msg, args=(cli_sock, ))
        receive_thread = threading.Thread(target=receive_msg, args=(cli_sock, ))
        send_thread.start()
        receive_thread.start()

    except KeyboardInterrupt:
        send_thread.join()
        receive_thread.join()
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
                cli_sock.send(msg_header + msg_code)
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

        snickname_length = int(snickname_header.decode('utf-8').strip())

        snickname = cli_sock.recv(snickname_length).decode('utf-8')

        msg_header = cli_sock.recv(HEADER_LENGTH)
        msg_length = int(msg_header.decode('utf-8').strip())
        msg = cli_sock.recv(msg_length).decode('utf-8')
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f'<{current_time}> [{snickname}]: {msg}')


if __name__ == '__main__':
    main()
