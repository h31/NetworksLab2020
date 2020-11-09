import socket
import threading
import datetime
import time


def local_time(message_time):
    timezone = -time.timezone / 3600
    message_time_to_time = datetime.datetime.strptime(message_time, "%H.%M.%S")
    message_time_local = message_time_to_time + datetime.timedelta(hours=timezone)
    message_time_format = datetime.datetime.strftime(message_time_local, "%H.%M.%S")
    return message_time_format


class ThreadReceive(threading.Thread):
    def __init__(self, server_socket):
        threading.Thread.__init__(self)
        self.ssocket = server_socket

    def run(self):
        while True:
            length_message = int(self.ssocket.recv(8).decode('UTF-8'))
            message_time = self.ssocket.recv(8).decode('UTF-8')
            chunks = []
            bytes_recd = 0
            while bytes_recd < length_message:
                chunk = self.ssocket.recv(length_message)
                if chunk == b'':
                    raise RuntimeError("socket connection broken")
                chunks.append(chunk)
                bytes_recd = bytes_recd + len(chunk)
            data = b''.join(chunks)
            message_time = local_time(message_time)
            length_name = int(self.ssocket.recv(8).decode('UTF-8'))
            name = self.ssocket.recv(length_name).decode('UTF-8')
            print(message_time + "[" + name + "]: " + data.decode("UTF-8"))


#SERVER = "51.15.130.137"
SERVER = "127.0.0.1"
PORT = 5001
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER, PORT))
login = input("Enter your login: ")
client.send(bytes(login, 'UTF-8'))
thread_receive = ThreadReceive(client)
thread_receive.start()
while True:
    out_data = bytes(input(), 'UTF-8')
    length = '{:08d}'.format(len(out_data))
    client.send(bytes(str(length), 'UTF-8'))
    client.send(bytes(datetime.datetime.utcnow().strftime("%H.%M.%S"), 'UTF-8'))
    client.send(out_data)
    if out_data == 'leave chat':
        break
client.shutdown(socket.SHUT_WR)
client.close()
