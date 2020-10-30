import datetime
import socket
import threading

username = input('Write your name: ')
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect(('127.0.0.1', 8080))
except ConnectionRefusedError:
    print("Server is offline")
    exit(0)
else:
    print("Connected to server\n")


def close_connection():
    client.shutdown(socket.SHUT_WR)
    client.close()
    exit(0)


def receive():
    while True:
        try:
            data = client.recv(2048)
        except ConnectionResetError:
            close_connection()
            return
        except Exception as ex:
            return
        else:
            print(data.decode('utf-8'))


def send():
    while True:
        data = input()
        if data == 'quit':
            close_connection()
        elif data != '':
            message = f"[{username}] {datetime.datetime.utcnow().strftime('%d/%m/%Y %H:%M')} :: {data}".encode('utf-8')
            client.send(message)


def main():
    threading.Thread(target=receive).start()
    threading.Thread(target=send).start()


if __name__ == '__main__':
    main()
