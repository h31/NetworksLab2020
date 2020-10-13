import os
import json
import threading
import socket
# import readline
HOST = '127.0.0.1'
PORT = 5008
H_SIZE = 10

#send to server
def send_to_sv(cli_socket):
    while True:

        inp = input()
        if inp == '!q':
            out_chat(cli_socket)
        else:
            normal_chat(cli_socket, inp)

#out of chat
def out_chat(cli_socket):
    msg = json.dumps({'type': 'O', 'msg': ''}).encode('UTF-8', 'error input')
    length_msg = f'{len(msg):< {H_SIZE}}'.encode()
    cli_socket.send(length_msg + msg)
    os._exit(0)

#chat as normal
def normal_chat(cli_socket, inp):
    msg = {'type': 'N', 'msg': inp}
    msg = json.dumps(msg).encode('UTF-8', 'error input')
    length_msg = f'{len(msg):< {H_SIZE}}'.encode()
    cli_socket.send(length_msg + msg)

#receive message from server
def rc_fr_sv(cli_socket):
    while True:
        length_msg = cli_socket.recv(H_SIZE)
        #server down suddenly(keyboard interupt)
        if (len(length_msg) == 0) or (length_msg == b'-1'):
            print(length_msg)
            print(len(length_msg))
            print('server down')
            cli_socket.close()
            os._exit(0)
        else:
            length_msg = int(length_msg)
            msg = cli_socket.recv(length_msg)
            msg = json.loads(msg.decode())
            if msg['type'] == 0:
                continue
            else:
                print(msg['msg'])

#client
def cl():
    cli_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cli_socket.connect((HOST, PORT))
    #keyboard interrupt when insert name of user
    while True:
        try:
            cli_name = input('Your Name(Shinkai Makoto):')
        except KeyboardInterrupt:
            out_chat(cli_socket)
            os._exit(0)
        if cli_name == '':
            cli_name = 'anony'
            break
        elif len(cli_name) > 32:
            print('>>NAME TOO LONG<<')
        else:
            break
    msg = json.dumps({'type': 'J', 'msg': cli_name}).encode('UTF-8','error input')
    message_header = f"{len(msg):<{H_SIZE}}".encode()
    cli_socket.send(message_header+msg)
    send_th = threading.Thread(target=send_to_sv, args=[cli_socket])
    send_th.start()
    rc_th = threading.Thread(target=rc_fr_sv, args=[cli_socket])
    rc_th.start()
    try:
        while 1:
            continue
    except KeyboardInterrupt:
        out_chat(cli_socket)

cl()
