import socket
import threading
import os
import select
import signal
from datetime import datetime, timezone

HOST = "127.0.0.1"
PORT = 5002
SIZE = 5
sockets_list = []
client_list = []
list_name = []
data = []
# accept client_socket
def accept_cli():
    cli_socket, cli_add = sv_socket.accept()
    cli_socket.setblocking(0)
    sockets_list.append(cli_socket)
    client_list.append(cli_socket)
    list_name.append("")
    data.append([0, b""])
    print("Accepted socket")


def isdone(cli_socket):
    indx = client_list.index(cli_socket)
    if len(data[indx][1]) == data[indx][0]:
        return True
    else:
        return False


# recv and send to all client except one(who send)
def recv_send_cli(cli_socket):
    indx = client_list.index(cli_socket)
    type_m = 1
    if isdone(cli_socket):
        length = cli_socket.recv(SIZE)
        msg = ""
        if not length:
            type_m = -1
        else:
            length = int(length) - SIZE
            type_m = int(cli_socket.recv(SIZE).decode("UTF-8"))
            data[indx][1] += cli_socket.recv(length)
            data[indx][0] = length
        # set name
    else:
        remain = data[indx][0] - len(data[indx][1])
        data[indx][1] += cli_socket.recv(remain)

    if isdone(cli_socket):
        msg = data[indx][1].decode("UTF-8")
        data[indx][0] = 0
        data[indx][1] = b""
        name = get_set_name(cli_socket, msg, type_m)
        time = str(
            datetime.now(timezone.utc).replace(tzinfo=timezone.utc).timestamp()
        ).ljust(20)
        # change message format
        msg_cli = format_msg(cli_socket, type_m, msg, time, name)
        send_to_client(cli_socket, type_m, name, msg_cli)
        if type_m == -1:
            print(f"{name} Out")
            remove_client(cli_socket)


def remove_client(cli_socket):
    list_name.pop(client_list.index(cli_socket))
    data.pop(client_list.index(cli_socket))

    client_list.remove(cli_socket)
    sockets_list.remove(cli_socket)


def send_to_client(cli_socket, type_m, name, msg):
    for client in client_list:
        if client != cli_socket:
            length = f"{len(msg):<{SIZE}}".encode("UTF-8")
            client.send(length + msg)


def get_set_name(cli_socket, msg, type_m):
    if type_m == 2:
        indx = client_list.index(cli_socket)
        list_name[indx] = msg
    return list_name[client_list.index(cli_socket)]


def format_msg(cli_socket, type_m, msg, time, name):
    new_format = ""
    # '2'<-> join message
    if type_m == 2:
        new_format = f"{time}\t--- {name} JOIN---"
    # '1'<-> normal message
    elif type_m == 1:
        new_format = f"{time}[{name}]:{msg}"
    # '-1'<-> out message
    elif type_m == -1:
        new_format = f"{time}\t--- {name} OUT---"
    return new_format.encode("UTF-8")


def server_down():
    for cli in client_list:
        cli.send(f"-1".encode("UTF-8"))
    sv_socket.close()
    os._exit(0)


def signal_handler(signal, frame):
    server_down()


# server
sv_socket = socket.socket()


def sv():
    global sv_socket
    sv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # reusable right after sudden shutdown
    sv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sv_socket.bind((HOST, PORT))
    sv_socket.setblocking(0)
    sv_socket.listen(5)
    sockets_list.append(sv_socket)
    signal.signal(signal.SIGINT, signal_handler)
    while 1:
        read_s, write_s, error_s = select.select(sockets_list, [], sockets_list)
        print(read_s)
        for s in read_s:
            if s == sv_socket:
                accept_cli()
            else:
                recv_send_cli(s)
        for s in error_s:
            remove_client(s)


sv()
