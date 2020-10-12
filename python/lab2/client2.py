import errno
import socket
import threading
import time
import sys

CODE = 'utf-8'
HEADER_LEN = 10
IP = 'localhost'
PORT = 5001


def client2():
    # Нам нужно кодировать имя пользователя в байтах
    nickname = input("Enter your nickname: ").encode(CODE)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    # Устанавливаем соединение в неблокирующее состояние, чтобы вызов .recv () не был заблокирован
    # Далее просто будем обрабатывать исключения
    client_socket.setblocking(False)
    # Подготавливаем заголовок фиксированного размера, который мы также кодируем в байтах
    nick_header = f"{len(nickname):<{HEADER_LEN}}".encode(CODE)
    client_socket.send(nick_header + nickname)
    threading.Thread(target=receive, args=(client_socket,)).start()
    threading.Thread(target=send, args=(client_socket,)).start()


def receive(socket):
    while True:
        # Теперь мы хотим перебрать полученные сообщения (их может быть больше одного) и вывести их
        try:
            # Получим заголовок, содержащий длину имени пользователя (размер константный)
            nick_header = socket.recv(HEADER_LEN)
            # print(nick_header)
            # Если мы не получили данных, сервер корректно закрыл соединение (socket.close () или socket.SHUT_RDWR)
            if not len(nick_header):
                print("Connection was closed by the server")
                sys.exit()
            nickname_len = int(nick_header.decode(CODE).strip())
            nickname = socket.recv(nickname_len).decode(CODE)
            # Теперь то же самое для сообщения (поскольку мы получили имя пользователя, мы получили
            # все сообщение, нет необходимости проверять, имеет ли оно какую-либо длину)
            msg_header = socket.recv(HEADER_LEN)
            # print(msg_header)
            msg_len = int(msg_header.decode(CODE).strip())

            message = socket.recv(msg_len).decode(CODE)
            msg_time = time.strftime("%H:%M", time.localtime())
            print(f'<{msg_time}> [{nickname}]: {message}')
        # Это нормально для неблокирующих соединений - когда нет входящих данных, может возникнуть ошибка
        # Некоторые операционные системы укажут, что используют AGAIN, а некоторые используют код ошибки WOULDBLOCK
        # Мы собираемся проверить оба - если один из них - это ожидаемый, означает отсутствие входящих данных,
        # продолжаем как обычно. Если у нас другой код ошибки - что-то случилось
        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print('Error: {}'.format(str(e)))
                sys.exit()
            # Мы просто ничего не получили
            continue

        except Exception as e:
            # Другие ошибки, значит что-то случилось, выходим
            print('Error: '.format(str(e)))
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
            continue

        except:
            # socket.shutdown(socket.SHUT_RDWR)
            # socket.close()
            exit(0)
            return


client2()
