import socket
import selectors
import sys

SERVER = "0.0.0.0"
PORT = 1339

FORMAT = 'utf-8'
SERVER_MASSAGE = "SERVER DEAD"
DISCONNECT_MESSAGE = "!DISCONNECT"

HEADER = 64
serv = None
names = {}
sel = selectors.DefaultSelector()


def start_server():
    print("[STARTING] server is starting...")
    print(f"[LISTENING] Server is listening on {SERVER}")
    global serv_socket
    serv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv_socket.bind((SERVER, PORT))
    serv_socket.listen()
    serv_socket.setblocking(False)
    sel.register(fileobj=serv_socket, events=selectors.EVENT_READ, data=new_connection)


def send_all_world(msg):
    msg = f'{len(msg):<{HEADER}}'.encode(FORMAT) + msg
    for client in names.keys():
        client.send(msg)


def close_server():
    global names
    exit_msg= f"{len(SERVER_MASSAGE):<{HEADER}}"
    msg = exit_msg
    send_all_world(msg.encode(FORMAT))
    for c in names.keys():
        c.close()
        sel.unregister(c)
    names = {}
    serv.close()


def client_disconnect(client_socket, user):
    msg = "You are disconnected from the server"
    exit_msg_header = f"{len(msg):<{HEADER}}"
    exit_msg = exit_msg_header + msg
    client_socket.send(exit_msg.encode(FORMAT))

    client_socket.close()
    del names[client_socket]
    msg = "%s : !DISCONNECT" % user
    sel.unregister(client_socket)
    send_all_world(msg.encode(FORMAT))


def handle_client(client):
    try:
        if client not in names.keys():
            msg_length = int(client.recv(HEADER).decode(FORMAT))
            name = client.recv(msg_length).decode(FORMAT)
            names[client] = name
            msg = "To quit from chat type !DISCONNECT"
            msg = f"{len(msg):<{HEADER}}" + msg
            client.send(msg.encode(FORMAT))
        else:
            msg_length = int(client.recv(HEADER).decode(FORMAT))
            msg = client.recv(msg_length)
            nnn = msg_length - len(msg)
            while nnn != 0:
                try:
                    msg += client.recv(msg_length)
                    nnn = msg_length - len(msg)
                except:
                    continue

            msg = [m.decode(FORMAT) for m in msg.split(b'\0')]

            if msg[2] != DISCONNECT_MESSAGE:
                time = msg[0].encode(FORMAT)
                user = msg[1].encode(FORMAT)
                text = msg[2].encode(FORMAT)
                msg = b'\0'.join([time, user, text])
                send_all_world(msg)
            else:
                client_disconnect(client, names[client])
    except:
        client_disconnect(client, names[client])


def new_connection(servsocket):
    conn, addr = servsocket.accept()
    conn.setblocking(False)
    sel.register(fileobj=conn, events=selectors.EVENT_READ, data=handle_client)
    conn.setblocking(False)
    print(f"[NEW CONNECTION] {addr} connected.")


def events():
    try:
        while True:
            events = sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj)
    except:
        close_server()
        sys.exit(0)

if __name__ == '__main__':
    start_server()
    events()
