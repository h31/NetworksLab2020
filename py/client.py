import os
import json
import threading
import socket
import readline
HOST = '127.0.0.1'
PORT = 5003
M_SIZE = 1024

#send to server


def send_to_sv(cli_socket):
    while True:

        inp = input()
        if inp == 'out_chat':
            out_chat(cli_socket)
        else:
            normal_chat(cli_socket, inp)

#out of chat


def out_chat(cli_socket):
    msg = {'type': 'O', 'msg': ''}
    cli_socket.send(json.dumps(msg).encode('utf8', 'error input'))
    os._exit(0)

#chat as normal


def normal_chat(cli_socket, inp):
    msg = {'type': 'N', 'msg': inp}
    msg = json.dumps(msg).encode('utf8', 'error input')
    if len(msg) > 1024:
        print('>>>MESSAGE TOO LONG. CAN NOT SEND')
        return
    cli_socket.send(msg)

#receive message from server


def rc_fr_sv(cli_socket):
    while True:
        msg = cli_socket.recv(M_SIZE)
        #server down suddenly(keyboard interupt)
        if (msg == b'-1') or (len(msg) == 0):
            print('server down')
            cli_socket.close()
            os._exit(0)
        print(msg.decode())

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
    msg = {'type': 'J', 'msg': cli_name}
    cli_socket.send(json.dumps(msg).encode('utf8', 'error input'))
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

