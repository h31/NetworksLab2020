import os
import threading
import socket
import signal
from datetime import datetime, timezone

# import readline
HOST = "127.0.0.1"
PORT = 5003
SIZE = 4

def send_to_sv():
    while True:
        
        inp = input()
        
        if inp == "!q":
            out_chat()
        elif inp == "":
            continue
        else:
            normal_chat(inp)

# out of chat
def out_chat():
    msg = f"{'-1'.ljust(SIZE)}".encode("UTF-8")
    length_msg = f"{len(msg):<{SIZE}}".encode("UTF-8")    
    cli_socket.send(length_msg + msg)
    os._exit(0)


# chat as normal
def normal_chat(inp):
    msg = f"{('1'.ljust(SIZE) +inp)}".encode("UTF-8")
    length_msg = f"{len(msg):<{SIZE}}".encode("UTF-8")
    cli_socket.send(length_msg + msg)


# receive message from server
def rc_fr_sv():
    while True:
        length_msg = cli_socket.recv(SIZE)
        # server down suddenly(keyboard interupt)
        if (len(length_msg) == 0) or (length_msg == b"-1"):
            print("server down")
            cli_socket.close()
            os._exit(0)
        else:
            length_msg = int(length_msg)
            time =float(cli_socket.recv(20).decode("UTF-8"))
            time = datetime.fromtimestamp(time).strftime("%H:%M")
            msg = cli_socket.recv(length_msg-20).decode("UTF-8")
            print(f'<{time}>{msg}')

def signal_handler(signal, frame):
    out_chat()

cli_socket=socket.socket()
# client
def cl():
    global cli_socket
    cli_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cli_socket.connect((HOST, PORT))
    # keyboard interrupt 
    signal.signal(signal.SIGINT, signal_handler)
    while True:
        cli_name = input("Your Name(default = anony):")
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
    send_th = threading.Thread(target=send_to_sv, args=[])
    send_th.start()
    rc_th = threading.Thread(target=rc_fr_sv, args=[])
    rc_th.start()
    
cl()