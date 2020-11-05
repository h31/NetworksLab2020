import socket
import select


class ReceiveMessage:

    def __init__(self, client_socket: socket, client_address):
        self.socket = client_socket
        self.address = client_address
        self.messages = []  # список сообщений, хранит словари с ключами message и time
        self.name = None  # хранит имя пользователя
        self.time = None  # хранит сообщение о времени
        self.buffer_message = b''  # хранит полученные символы от пользователя
        self.message_length = b''  # длина получаемого сообщения
        self.actual_length = 0  # текущее количество принятых символов
        # далее идут флаговые переменные
        self.end_receive = False  # сообщает, если приём окончен
        self.end_receive_length = False  # сообщает, если приём длины сообщения окончен
        self.end_receive_time = False  # сообщает, если приём сообщения о времени окончен
        self.end_receive_message = False  # сообщает, если приём сообщения от пользователя окончен

    '''Метод receive_name устанавливает атрибут name в соответсвии с именем пользователя. Вызывается метод receive. Как
    только приём окончен, устанавливает имя, сбрасывает флаги окончания приёма и окончания приёма длины, обнуляет 
    атрибут buffer_message'''

    def receive_name(self):
        self.receive()
        if self.end_receive:
            self.name = self.buffer_message.decode('utf-8')
            self.buffer_message = b''
            self.message_length = b''
            self.end_receive = False
            self.end_receive_length = False

    '''Метод receive_time устанавливает атрибут time в соответсвии с временем пользователя. Вызывается метод receive. 
    Как только приём окончен, устанавливает имя, сбрасывает флаги окончания приёма и окончания приёма длины, обнуляет 
    атрибут buffer_message, взводит флаг об окончании приёма времени'''

    def receive_time(self):
        self.receive()
        if self.end_receive:
            self.time = self.buffer_message.decode('utf-8')
            self.buffer_message = b''
            self.message_length = b''
            self.end_receive_length = False
            self.end_receive = False
            self.end_receive_time = True

    '''Метод receive_message добавляет в атрибут messages время и сообщение пользователя. Вызывается метод 
    receive. Как только приём сообщения пользователя окончен, добавляет в список сообщений словарь с ключами
    time и message значения времени и сообщения соотвественно, сбрасывает флаги окончания приёма и окончания приёма 
    длины, обнуляет атрибут buffer_message, взводит флаг об окончании приёма сообщения'''

    def receive_message(self):
        self.receive()
        if self.end_receive:
            message = self.buffer_message.decode('utf-8')
            self.messages.append({'time': self.time, 'message': message})
            self.buffer_message = b''
            self.message_length = b''
            self.end_receive_length = False
            self.end_receive = False
            self.end_receive_message = True

    '''Метод receive принимает посылку от пользователя. В самом начале, если не поднят флаг об окончании приёма длины,
    с помощью метода receive_length принимает длину. Иначе, получает сообщение от пользователя. Если текущее количество
    принятых символов равно общему ожидаемому количеству, считаем, что сообщение полностью получено. Взводит флаг
    об окончании приёма, обнуляет текущее количество принятых символов'''

    def receive(self):
        if not self.end_receive_length:
            self.receive_length()
        else:
            length = int(self.message_length.decode('utf-8'))
            self.buffer_message += self.confirmation_of_message(length - self.actual_length)
            if self.actual_length == length:
                self.end_receive = True
                self.actual_length = 0

    '''Метод receive_length служит для получения сообщения о длине. Получает сообщение с помощью 
    confirmation_of_message. Если текущее количество принятых символов равно общему ожидаемому количеству, 
    считаем, что сообщение о длине полностью получено. Взводит флаг об окончании приёма длины, обнуляет текущее 
    количество принятых символов'''

    def receive_length(self):
        self.message_length += self.confirmation_of_message(16 - self.actual_length)
        if self.actual_length == 16:
            self.end_receive_length = True
            self.actual_length = 0

    '''Метод confirmation_of_message контролирует получение полного сообщения от пользователя'''

    def confirmation_of_message(self, length: int):
        chunks = []
        while self.actual_length < length:
            chunk = self.socket.recv(length)
            if chunk == b'':
                break
            chunks.append(chunk)
            self.actual_length += len(chunk)
        return b''.join(chunks)

    '''Метод send_message служит для отправки сообщений клиентам. На вход принимает словарь клиентов. Производит
    кодирование времени, имени и сообщения пользователя. Находит длину для каждого из них. Удаляет закодированное
    сообщение из списка сообщений. Далее отправляет сообщения согласно протоколу'''

    def send_message(self, clients: dict):
        time = self.messages[0]['time'].encode('utf-8')
        length_time = convert_to_sixteen_bytes(time).encode('utf-8')
        name = self.name.encode('utf-8')
        length_name = convert_to_sixteen_bytes(name).encode('utf-8')
        message = self.messages[0]['message'].encode('utf-8')
        length_message = convert_to_sixteen_bytes(message).encode('utf-8')
        del self.messages[0]
        for client in clients.keys():
            if self.socket != client:
                client.send(length_time)
                client.send(time)
                client.send(length_name)
                client.send(name)
                client.send(length_message)
                client.send(message)


def convert_to_sixteen_bytes(message):
    return '{:016d}'.format(len(message))


def main():
    print('Сервер запущен')
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', 5001))
    server.listen(5)
    server.setblocking(False)
    inputs = [server]
    outputs = []
    clients = {}

    while True:
        readable, writable, exceptional = select.select(inputs, outputs, [])
        for s in readable:
            if s == server:
                conn, addr = server.accept()
                conn.setblocking(False)
                clients[conn] = ReceiveMessage(conn, addr)
                print('Подключен:', addr)
                inputs.append(conn)
            else:
                if clients[s].name is None:
                    clients[s].receive_name()
                elif not clients[s].end_receive_time:
                    clients[s].receive_time()
                elif not clients[s].end_receive_message:
                    clients[s].receive_message()
                if clients[s].messages:
                    if clients[s].messages[0]['message'] == 'exit()':
                        print('Отключен', clients[s].address)
                        del clients[s]
                        inputs.remove(s)
                        s.close()
                    else:
                        clients[s].send_message(clients)
                        clients[s].end_receive_time = False
                        clients[s].end_receive_message = False


if __name__ == '__main__':
    main()
