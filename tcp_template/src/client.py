import socket
import threading


class ThreadReceive(threading.Thread):
    def __init__(self, server_socket):
        threading.Thread.__init__(self)
        self.ssocket = server_socket

    def run(self):
        while True:
            length_message = int(self.ssocket.recv(8).decode('UTF-8'))
            chunks = []
            bytes_recd = 0
            while bytes_recd < length_message:
                chunk = self.ssocket.recv(length_message)
                if chunk == b'':
                    raise RuntimeError("socket connection broken")
                chunks.append(chunk)
                bytes_recd = bytes_recd + len(chunk)
            data = b''.join(chunks)
            print(data.decode("UTF-8"))


SERVER = "127.0.0.1"
PORT = 5001
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER, PORT))
login = input("Enter your login: ")
client.send(bytes(login, 'UTF-8'))
thread_receive = ThreadReceive(client)
thread_receive.start()
while True:
    out_data = input()
    length = '{:08d}'.format(len(out_data))
    client.send(bytes(str(length), 'UTF-8'))
    client.send(bytes(out_data, 'UTF-8'))
    if out_data == 'leave chat':
        break
client.shutdown(socket.SHUT_WR)
client.close()
