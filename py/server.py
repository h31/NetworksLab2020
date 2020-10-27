import socket
import threading
from datetime import datetime
import os
import random
import select
HOST = "127.0.0.1"
PORT = 5001
SIZE = 4
sockets_list=[]
client_list = []
list_name = []


def sv():
    sv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # reusable right after sudden shutdown
    sv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sv_socket.bind((HOST, PORT))
    sv_socket.listen(5)
    sockets_list.append(sv_socket)
    # keyboard Interrupt
    try:
        while 1:
            read_s, write_s, error_s= select.select(sockets_list,[],[])
            for s in read_s:
                if s==sv_socket:
                    accept_cli(sv_socket)
                else:
                    recv_send_cli(s)
                    
    except KeyboardInterrupt:
        for cli in client_list:
            cli.send(f"-1".encode())
        sv_socket.close()
        os._exit(0)



# accept client_socket
def accept_cli(sv_socket):
    cli_socket, cli_add = sv_socket.accept()
    sockets_list.append(cli_socket)
    client_list.append(cli_socket)
    list_name.append("")
    print("Accepted socket")

# recv and send to all client except one(who send)
def recv_send_cli(cli_socket):
    length = int(cli_socket.recv(SIZE))
    type_m = int(cli_socket.recv(SIZE).decode("UTF-8"))
    msg = cli_socket.recv(length).decode("UTF-8")
    # set name
    name = get_set_name(cli_socket, msg, type_m)
    # set time
    time = datetime.now().strftime("%H:%M")
    # change message format
    msg_cli = format_msg(cli_socket, type_m, msg, time, name)
    send_to_client(cli_socket, type_m, name, msg_cli)
    if type_m == -1:
        print('')
        list_name.pop(client_list.index(cli_socket))
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
        while 1:
            temp = msg + "-" + str(random.randint(0,100))
            if temp not in list_name:
                break
        list_name[indx] = temp
    return list_name[client_list.index(cli_socket)]


def format_msg(cli_socket, type_m, msg, time, name):
    new_format = ""
    #'2'<-> join message
    if type_m == 2:
        new_format = f"\t<<<{name} JOIN>>>"
    #'1'<-> normal message
    elif type_m == 1:
        new_format = f"<{time}>[{name}]:{msg}"
    #'-1'<-> out message
    elif type_m == -1:
        print('ok')
        new_format = f"\t<<<{name}>>> OUT"
    return new_format.encode("UTF-8")


# server


sv()