import socket
import threading
import time

CODE = 'utf-8'
HEADER_LEN = 10
IP = 'localhost'
PORT = 5001
# Лист подключенных clients - socket это ключ, user header и name это данные
clients_list = {}


# Для чтения данных используется функция recv, которой первым параметром нужно передать количество получаемых
# байт данных. Если столько байт, сколько указано, не пришло, а какие-то данные уже появились, она всё равно
# возвращает всё, что имеется, поэтому надо контролировать размер полученных данных.
# Тип возвращаемых данных — bytes. У этого типа есть почти все методы, что и у строк, но для того, чтобы использовать
# из него текстовые данные с другими строками (складывать, например, или искать строку в данных, или печатать),
# придётся декодировать данные (или их часть, если вы обработали байты и выделили строку)
# и использовать уже полученную строку.


def receive(socket):
    while True:
        try:
            # Получаем наш header, содержащий длину сообщения, размер константный
            msg_header = socket.recv(HEADER_LEN)
            # Если мы не получили данных, клиент корректно закрыл соединение (socket.close () или socket.SHUT_RDWR)
            if not msg_header:
                return False
            # Метод strip() возвращает копию строки, в которой все символы были удалены с начала и конца (пробелы)
            msg_len = int(msg_header.decode(CODE).strip())
            # Возвращаем объект заголовка сообщения и данных сообщения
            return {"header": msg_header, "data": socket.recv(msg_len)}
        except:
            # Если мы здесь, клиент резко закрыл соединение, например, нажав ctrl + c в своем скрипте
            return False


def server():
    # TCP почти всегда использует SOCK_STREAM, а UDP использует SOCK_DGRAM.
    # TCP (SOCK_STREAM) - это протокол, основанный на соединении. Соединение установлено, и обе стороны ведут
    # разговор до тех пор, пока соединение не будет прервано одной из сторон или сетевой ошибкой.
    # UDP (SOCK_DGRAM) - это протокол на основе дейтаграмм. Вы отправляете одну дейтаграмму и получаете один ответ,
    # а затем соединение разрывается.
    # socket.AF_INET — IPv4 usage

    serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Решение проблемы с Address already in use, вроде не возникало, но добавил
    serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serv_sock.bind((IP, PORT))

    # С помощью метода listen мы запустим для данного сокета режим прослушивания.
    # Метод принимает один аргумент — максимальное количество подключений в очереди.
    serv_sock.listen()
    print("Server was started!")

    while True:
        # мы можем принять подключение с помощью метода accept, который возвращает кортеж с двумя элементами:
        # новый сокет и адрес клиента. Именно этот сокет и будет использоваться для приема и посылки клиенту данных.
        client_socket, client_data = serv_sock.accept()
        client = receive(client_socket)

        if client:
            # Сохраняем имя пользователя и его заголовок
            clients_list[client_socket] = client
            print(f"Connection from {client_data[0]}:{client_data[1]} ; Nickname: {client['data'].decode(CODE)}")
            threading.Thread(target=handler, args=(client_socket, client,)).start()


def handler(socket, client):
    while True:
        message = receive(socket)
        local_time = str(int(time.time())).encode(CODE)
        l_time_header = f"{len(local_time):<{HEADER_LEN}}".encode(CODE)
        sender_time = {"header": l_time_header, "data": local_time}
        if not message or message['data'].decode(CODE) == "!exit":
            # Клиент отключился, удаляем его
            try:
                print(f"Connection was closed by {clients_list[socket]['data'].decode(CODE)}")
                del clients_list[socket]
                socket.shutdown(socket.SHUT_RDWR)
                socket.close()
                continue
            except:
                continue
        server_time = time.strftime("%H:%M", time.gmtime())
        print(
            f"Received message at {server_time} from {client['data'].decode(CODE)}: {message['data'].decode(CODE)}")
        for client_sock in clients_list:
            if client_sock != socket:
                # Мы повторно используем здесь заголовок сообщения, отправленный отправителем, и сохраненный
                # Заголовок имени пользователя, отправленный пользователем при подключении
                client_sock.send(
                    client['header'] + client['data'] + message['header'] + message['data'] + sender_time[
                        'header'] + sender_time['data'])


server()
