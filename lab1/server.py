import socket
from threading import Thread

PORT = 7556
HEADER = 64
SERVER = "0.0.0.0"
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER_MASSAGE = "SERVER DEAD"
dict = {}
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
CHECK = True


def send_all_world(msg):
    msg = f'{len(msg):<{HEADER}}'.encode('utf-8') + msg
    for client in dict.keys():
        client.send(msg)


def client_disconnect(client):
    msg = "You are disconnected from the server"
    exit_msg_header = f"{len(msg):<{HEADER}}"
    exit_msg = exit_msg_header + msg
    client.send(exit_msg.encode(FORMAT))
    client.close()
    dict.pop(client)

def handle_client(conn):
    connected = True
    global CHECK
    while connected and CHECK:
        try:
            if conn not in dict.keys():
                msg_length = int(conn.recv(HEADER).decode(FORMAT))
                name = conn.recv(msg_length).decode(FORMAT)
                dict[conn] = name
                msg = "To quit from chat type !DISCONNECT"
                msg = f"{len(msg):<{HEADER}}" + msg
                conn.send(msg.encode(FORMAT))
            else:
                msg_length = int(conn.recv(HEADER).decode('utf-8'))
                msg = conn.recv(msg_length)
                nnn = msg_length - len(msg)
                while nnn != 0:
                    msg += conn.recv(msg_length)
                msg = [m.decode(FORMAT) for m in msg.split(b'\0')]
                if msg[2] != DISCONNECT_MESSAGE:
                    time = msg[0].encode(FORMAT)
                    name = msg[1].encode(FORMAT)
                    text = msg[2].encode(FORMAT)
                    msg = b'\0'.join([time, name, text])
                    send_all_world(msg)
                else:
                    client_disconnect(conn)
                    connected = False

        except:
            print('you are disconnected from the server')
            send_all_world(DISCONNECT_MESSAGE)
            break

    print('this person remove')


def start():
    server.listen()
    while True:
        try:
            conn, addr = server.accept()
            print(f"[NEW CONNECTION] {addr} connected.")
            potok = Thread(target=handle_client, args=(conn,))
            potok.start()
        except:
            exit_msg = SERVER_MASSAGE
            send_all_world(exit_msg.encode(FORMAT))
            for c in dict.keys():
                c.close()
            dict.clear()
            server.close()


if __name__ == '__main__':
    print("[STARTING] server is starting...")
    print(f"[LISTENING] Server is listening on {SERVER}")
    start()
