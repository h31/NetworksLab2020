import socket
from select import select

CODE = 'utf-8'
HEADER_LEN = 10
IP = 'localhost'
PORT = 5001
# Лист подключенных clients - socket это ключ, user header и name это данные
clients_list = {}
sockets_list = []


# Для чтения данных используется функция recv, которой первым параметром нужно передать количество получаемых
# байт данных. Если столько байт, сколько указано, не пришло, а какие-то данные уже появились, она всё равно
# возвращает всё, что имеется, поэтому надо контролировать размер полученных данных.
# Тип возвращаемых данных — bytes. У этого типа есть почти все методы, что и у строк, но для того, чтобы использовать
# из него текстовые данные с другими строками (складывать, например, или искать строку в данных, или печатать),
# придётся декодировать данные (или их часть, если вы обработали байты и выделили строку)
# и использовать уже полученную строку.


def receive(socket):
    try:
        # Получаем наш header, содержащий длину сообщения, размер константный
        msg_header = socket.recv(HEADER_LEN)
        # Если мы не получили данных, клиент корректно закрыл соединение (socket.close () или socket.SHUT_RDWR)
        if not msg_header:
            return False
        # Метод strip() возвращает копию строки, в которой все символы были удалены с начала и конца строки (пробелы)
        msg_len = int(msg_header.decode(CODE).strip())
        # Возвращаем объект заголовка сообщения и данных сообщения
        return {"header": msg_header, "data": socket.recv(msg_len)}
    except:
        # Если мы здесь, клиент резко закрыл соединение, например, нажав ctrl + c в своем скрипте
        return False


def new_client(socket):
    # мы можем принять подключение с помощью метода accept, который возвращает кортеж с двумя элементами:
    # новый сокет и адрес клиента. Именно этот сокет и будет использоваться для приема и посылки клиенту данных.
    client_socket, client_data = socket.accept()
    client = receive(client_socket)
    # Добавить принятый сокет в список select()
    sockets_list.append(client_socket)
    # Сохраняем имя пользователя и его заголовок
    clients_list[client_socket] = client
    print(f"Connection from {client_data[0]}:{client_data[1]} ; Nickname: {client['data'].decode(CODE)}")


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
    sockets_list.append(serv_sock)
    print("Server was started!")

    # Функция select() даёт нам возможность одновременной проверки нескольких сокетов, чтобы увидеть, если у них данные,
    # ожидающие recv() или можете ли вы send() данные в сокет без блокирования. Данная функция работает в режиме
    # блокировки, пока либо не произойдут события, связанные с появлением возможности чтения или записи в сокеты,
    # либо не истечет время тайм аута, задаваемое для этого вызова. Аргументы функции select() имеют следующий смысл:
    # fd_set *readfds, fd_set *writefds, fd_set *exceptfds - это указатели на наборы дескрипторов сокетов,
    # предназначенных для операций чтения, записи и исключительных ситуаций

    while True:
        sockets, _, exceptions = select(sockets_list, [], sockets_list)
        for sock in sockets:
            if sock == serv_sock:
                new_client(sock)
            elif message := receive(sock):
                # Получить пользователя по уведомленному сокету, чтобы мы знали, кто отправил сообщение
                client = clients_list[sock]
                for client_sock in clients_list:
                    if client_sock != sock:
                        # Мы повторно используем здесь заголовок сообщения, отправленный отправителем, и сохраненный
                        # Заголовок имени пользователя, отправленный пользователем при подключении
                        print(f"Received message from {client['data'].decode(CODE)}: {message['data'].decode(CODE)}")
                        client_sock.send(client['header'] + client['data'] + message['header'] + message['data'])
            # Клиент отключился, удаляем его
            elif message is False:
                print(f"Connection was closed by {clients_list[sock]['data'].decode(CODE)}")
                sockets_list.remove(sock)
                del clients_list[sock]
        # Обработка некоторых исключений сокетов
        for sock in exceptions:
            sockets_list.remove(sock)
            del clients_list[sock]


server()
