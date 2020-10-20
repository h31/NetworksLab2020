import socket
import threading
import time
import sys

CODE = 'utf-8'
HEADER_LEN = 16
IP = 'localhost'
PORT = 5001


def client():
    # Нам нужно кодировать имя пользователя в байтах
    nickname = input("Enter your nickname: ").encode(CODE)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    # Подготавливаем заголовок фиксированного размера, который мы также кодируем в байтах
    nick_header = f"{len(nickname):<{HEADER_LEN}}".encode(CODE)
    client_socket.send(nick_header + nickname)
    threading.Thread(target=read, args=(client_socket,)).start()
    threading.Thread(target=send, args=(client_socket,)).start()


# receive обрабатывает части сообщения (ник, само сообщения, время отправки)
def receive(socket):
    while True:
        # Теперь мы хотим перебрать полученные сообщения (их может быть больше одного) и вывести их
        # Получим заголовок, содержащий длину имени пользователя (размер константный)
        header = socket.recv(HEADER_LEN)
        # print(header)
        # Если мы не получили данных, сервер корректно закрыл соединение (socket.close () или socket.SHUT_RDWR)
        if not len(header):
            print("Connection was closed by the server")
            sys.exit()
        part_len = int(header.decode(CODE).strip())
        return socket.recv(part_len).decode(CODE)


def read(socket):
    while True:
        try:
            nickname = receive(socket)
            message = receive(socket)
            msg_time = receive(socket)
            # производим учет времени отправителя и получателя
            user_time = time.strftime("%H:%M", (time.localtime(int(msg_time))))
            print(f'<{user_time}> [{nickname}]: {message}')

        except Exception as e:
            print('Error', str(e))
            sys.exit()


def send(socket):
    while True:
        try:
            message = input()
            # выход из чата после сообщения !exit
            # if message == "!exit":
            #     exit(0)
            #     socket.shutdown(socket.SHUT_RDWR)
            #     socket.close()
            #     return

            if message:
                # Закодировать сообщение в байты. Подготовить заголовок и преобразовать в байты,
                # как для имени пользователя ранее, затем отправить
                message1 = message
                message = message.encode(CODE)
                msg_header = f"{len(message):<{HEADER_LEN}}".encode(CODE)
                socket.send(msg_header + message)
                if message1 == "!exit":
                    socket.shutdown(socket.SHUT_RDWR)
                    socket.close()
                    exit(0)
                    return


        except EOFError as e:
            print("Incorrect input")
            continue

        except:
            exit(0)
            return


client()
