import os
import threading
import socket

# import readline
HOST = "127.0.0.1"
PORT = 5001
SIZE = 4

# send to server
def send_to_sv(cli_socket):
    while True:
        inp = input()
        if inp == "!q":
            out_chat(cli_socket)
        elif inp == "":
            continue
        else:
            normal_chat(cli_socket, inp)


# out of chat
def out_chat(cli_socket):
    msg = f"{'-1'.ljust(SIZE)}".encode("UTF-8")
    length_msg = f"{len(msg):<{SIZE}}".encode("UTF-8")    
    cli_socket.send(length_msg + msg)
    os._exit(0)


# chat as normal
def normal_chat(cli_socket, inp):
    msg = f"{('1'.ljust(SIZE) +inp)}".encode("UTF-8")
    length_msg = f"{len(msg):<{SIZE}}".encode("UTF-8")
    cli_socket.send(length_msg + msg)


# receive message from server
def rc_fr_sv(cli_socket):
    while True:
        length_msg = cli_socket.recv(SIZE)
        # server down suddenly(keyboard interupt)
        if (len(length_msg) == 0) or (length_msg == b"-1"):
            print("server down")
            cli_socket.close()
            os._exit(0)
        else:
            length_msg = int(length_msg)
            msg = cli_socket.recv(length_msg).decode("UTF-8")
            print(msg)


# client
def cl():
    cli_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cli_socket.connect((HOST, PORT))
    # keyboard interrupt when insert name of user
    while True:
        try:
            cli_name = input("Your Name(default = anony):")
        except KeyboardInterrupt:
            out_chat(cli_socket)
            os._exit(0)
        if cli_name == "":
            cli_name = "anony"
            break
        elif len(cli_name) > 32:
            print(">>NAME TOO LONG<<")
        else:
            break
    msg = f"{'2'.ljust(SIZE)+cli_name}".encode("UTF-8")
    length_msg = f"{len(msg):<{SIZE}}".encode("UTF-8")
    cli_socket.send(length_msg + msg)
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