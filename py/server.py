import socket
import threading
import json
from datetime import datetime
import os

HOST = '127.0.0.1'
PORT = 5008
H_SIZE = 10
client_list = []
list_name = []

#accept client_socket
def accept_cli(sv_socket):
    while True:
        cli_socket, cli_add = sv_socket.accept()
        print
        client_list.append(cli_socket)
        list_name.append(str(cli_add[1] % 8))
        print('Accepted socket')
        send_th = threading.Thread(target=recv_send_cli, args=[cli_socket])
        send_th.start()

#send to all client except one(who send)
def recv_send_cli(cli_socket):
    while True:
        length_msg = cli_socket.recv(H_SIZE)
        if (len(length_msg) == 0):
            msg = {'type': 'O', 'msg': ''}
        else:
            length_msg = int(length_msg)
            msg = cli_socket.recv(length_msg)
            msg = json.loads(msg.decode())
        # set name of client for the others can see
        if msg['type'] == 'J':
            list_name[client_list.index(
                cli_socket)] = msg["msg"] + "-" + list_name[client_list.index(cli_socket)]
            print(
                f'Client {list_name[client_list.index(cli_socket)]} send msg: JOIN')
        msg_to_cli = ''
        #with each type of message
        if msg['type'] == 'J':
            msg_to_cli = json.dumps(
                {'type': 1, 'msg': f'\t<<<{msg["msg"]}>>> JOIN'}).encode('UTF-8')
        elif msg['type'] == 'N':
            if msg["msg"] == '':
                msg_to_cli = json.dumps({'type': 0, 'msg': ''}).encode('UTF-8')
            else:
                msg_to_cli = json.dumps(
                    {'type': 1, 'msg': f'<{datetime.now().strftime("%H:%M")}>[{list_name[client_list.index(cli_socket)]}]:{msg["msg"]}'}).encode('UTF-8')
        elif msg['type'] == 'O':
            msg_to_cli = json.dumps(
                {'type': 1, 'msg': f'\t <<<{list_name[client_list.index(cli_socket)]}>>> OUT'}).encode()
        #send to client
        for client in client_list:
            if client != cli_socket:
                length_msg = f'{len(msg_to_cli):< {H_SIZE}}'.encode()
                client.send(length_msg + msg_to_cli)
        if msg['type'] == 'O':
            print(f'Client {list_name[client_list.index(cli_socket)]} OUT')
            list_name.pop(client_list.index(cli_socket))
            client_list.remove(cli_socket)
            return 1

#server
def sv():
    sv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #reuse able
    sv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sv_socket.bind((HOST, PORT))
    sv_socket.listen(5)
    accept_th = threading.Thread(target=accept_cli, args=[sv_socket])
    accept_th.start()

    #keyboard Interrupt
    try:
        while 1:
            continue
    except KeyboardInterrupt:
        for cli in client_list:
            cli.send(f'-1'.encode())
        sv_socket.close()
        os._exit(0)

sv()
