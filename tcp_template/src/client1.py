import datetime
import socket
import threading

HEADER_LENGTH = 5

username = input('Write your name: ')
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    # client.connect(('127.0.0.1', 8080))
    client.connect(('51.15.130.137', 8080))
except ConnectionRefusedError:
    print("Server is offline")
    exit(0)
else:
    print("Connected to server\n")


def close_connection():
    client.shutdown(socket.SHUT_WR)
    client.close()
    exit(0)


def receive_bytes(length):
    received = 0
    message = ''
    while True:
        try:
            data = client.recv(length - received)
            if received < length:
                print(f"receiving data: {data}")
                message += data.decode('utf-8')
                received += len(data)
            elif message == b'':
                close_connection()
            else:
                print(f"received: {message}")
                return message
        except Exception as ex:
            print(ex)
            return


def receive():
    while True:
        try:
            data = client.recv(HEADER_LENGTH)
            print(f"received {data}")
            message_length = int(data.decode('utf-8').strip())
            message = receive_bytes(message_length)
            if not message:
                close_connection()
            else:
                print(message)
        except ConnectionResetError:
            close_connection()
            return
        except Exception as ex:
            print(ex)


def send_bytes(data):
    message = data.encode("utf-8")
    length = len(message)
    header = f"{length:<{HEADER_LENGTH}}".encode('utf-8')
    message = header + message
    sent = 0
    while sent < length:
        _ = client.send(message[sent:])
        if _ == 0:
            raise RuntimeError("Socket connection broken")
        print(f"sent: {message[sent:]}")
        sent = sent + _


def send():
    while True:
        data = input()
        if data != '':
            data = f"[{username}] {datetime.datetime.utcnow().strftime('%d/%m/%Y %H:%M')} :: {data}"
            send_bytes(data)


def main():
    threading.Thread(target=receive).start()
    threading.Thread(target=send).start()


if __name__ == '__main__':
    main()
