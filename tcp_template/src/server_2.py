import socket
import select


def receive_message(receive_socket: socket):
    length = confirmation_of_message(receive_socket, 16)
    if length == '':
        return ''
    message = confirmation_of_message(receive_socket, int(length))
    return message


def confirmation_of_message(receive_socket: socket, length: int):
    recd = 0
    chunks = []
    while recd < length:
        chunk = receive_socket.recv(length)
        if chunk == b'':
            break
        chunks.append(chunk)
        recd += len(chunk)
    result = b''.join(chunks).decode('utf-8')
    return result


def send_message(messages, clients, socket_to):
    address_from = messages[0]['socket']
    time_message = messages[0]['time'].encode('utf-8')
    length_time_message = convert_to_sixteen_bytes(time_message).encode('utf-8')
    msg = messages.pop(0)['message'].encode('utf-8')
    length_msg = convert_to_sixteen_bytes(msg).encode('utf-8')
    name = clients[address_from][1].encode('utf-8')
    length_name = convert_to_sixteen_bytes(name).encode('utf-8')
    if socket != address_from:
        socket_to.send(length_time_message)
        socket_to.send(time_message)
        socket_to.send(length_name)
        socket_to.send(name)
        socket_to.send(length_msg)
        socket_to.send(msg)


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
    messages = []
    clients = {}
    while True:
        readable, writable, exceptional = select.select(inputs, outputs, inputs)
        for s in readable:
            if s is server:
                conn, addr = server.accept()
                print('Подключен:', addr)
                conn.setblocking(False)
                inputs.append(conn)
                name = receive_message(conn)
                clients[conn] = (conn, name)
            else:
                time_message = receive_message(s)
                message = receive_message(s)
                if message == 'exit()':
                    del clients[s]
                    inputs.remove(s)
                    if s in outputs:
                        outputs.remove(s)
                    s.close()
                else:
                    messages.append({'socket': s, 'message': message, 'time': time_message})
                    if s not in outputs:
                        outputs.append(s)

        for s in writable:
            if messages:
                send_message(messages, clients, s)


if __name__ == '__main__':
    main()