import socket
import threading
import json
from datetime import datetime
import os

HOST ='127.0.0.1'
PORT =5001
M_SIZE=1024
client_list=[]

#accept client_socket
def accept_cli(sv_socket): 
    while True:
        cli_socket, cli_add= sv_socket.accept()
        client_list.append(cli_socket)
        print('Accepted socket')
        send_th=threading.Thread(target=send_cli,args=[cli_socket])        
        send_th.start()

#send to all client except one(who send)        
def send_cli(cli_socket):
    while True:
       # print(cli_socket)
        msg = cli_socket.recv(M_SIZE)
        msg = json.loads(msg.decode())
        for client in client_list:
            if client != cli_socket:
                if msg['type']=='J':
                    client.send(f'\t<<<{msg["cli_name"]}>>> JOIN'.encode() )
                    print(f'Client {msg["cli_name"]} send msg: JOIN')
                elif msg['type']=='N':
                    if msg["msg"]=='':
                        continue
                    client.send(f'<{datetime.now().strftime("%H:%M")}>[{msg["cli_name"]}]:{msg["msg"]}'.encode())
                    print(f'Client {msg["cli_name"]} send msg: {msg["msg"]}')
                elif msg['type']=='O':
                    #if msg["cli_name"]=='':
                    client.send(f'\t <<<{msg["cli_name"]}>>> OUT'.encode())
                    print(f'Client {msg["cli_name"]} OUT')

        if msg['type']=='O':
            client_list.remove(cli_socket)
            cli_socket.close()            
            return 1            
#server
def sv():
    sv_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sv_socket.bind((HOST,PORT))
    sv_socket.listen(5)
    accept_th =threading.Thread(target=accept_cli, args=[sv_socket])
    accept_th.start()

    #keyboard Interrupt
    try:
        while 1:
            continue
    except KeyboardInterrupt:
        sv_socket.close()
        for cli in client_list:
            cli.send(f'-1'.encode())
            cli.close()
        os._exit(0)
sv()