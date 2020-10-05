import socket
import threading
import json
import sys
import os
HOST ='127.0.0.1'
PORT =5001
M_SIZE=1024

#send to server
def send_to_sv(cli_socket,cli_name):
    while True:
        inp = input()
        if inp=='out_chat':
            out_chat(cli_socket,cli_name)
        else:
            normal_chat(cli_socket,cli_name,inp)
    
#out of chat
def out_chat(cli_socket,cli_name):
    msg={'type':'O','cli_name':cli_name,'msg':''}
    cli_socket.send(json.dumps(msg).encode('utf8', 'error input'))   
    os._exit(0)

#chat as normal
def normal_chat(cli_socket,cli_name,inp):
    msg={'type':'N','cli_name':cli_name,'msg':inp}  
    cli_socket.send(json.dumps(msg).encode('utf8', 'error input')) 

#recive message from server
def rc_fr_sv(cli_socket):
    while True:
        msg=cli_socket.recv(M_SIZE)
        #server down suddenlly(keyboard interupt)
        if msg==b'-1':
                print('server down')
                return -1        
        print(msg.decode())

#client
def cl():
    cli_socket= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cli_socket.connect((HOST,PORT)) 
    #keyboard iterrupt when insert name of user
    try:
        cli_name= input('Your Name(Shinkai Makoto):')
    except KeyboardInterrupt:
        out_chat(cli_socket,'')
        os._exit()
    msg={'type':'J','cli_name':cli_name,'msg':''}
    cli_socket.send(json.dumps(msg).encode('utf8', 'error input'))   
    send_th = threading.Thread(target=send_to_sv, args=[cli_socket,cli_name])
    send_th.start()
    rc_th=threading.Thread(target=rc_fr_sv, args=[cli_socket])
    rc_th.start()
    try:
        while 1:
            continue
    except KeyboardInterrupt:
        out_chat(cli_socket,cli_name)
cl()