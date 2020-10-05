import socket
import threading
import json
from datetime import datetime
import os

HOST ='127.0.0.1'
PORT =5002
M_SIZE=1024
client_list=[]
list_name=[]
#accept client_socket
def accept_cli(sv_socket): 
    while True:
        cli_socket, cli_add= sv_socket.accept()
        print 
        client_list.append(cli_socket)
        list_name.append(str(cli_add[1]%100))
        print('Accepted socket')
        send_th=threading.Thread(target=send_cli,args=[cli_socket])  
      
        send_th.start()

#send to all client except one(who send)        
def send_cli(cli_socket):
    while True:
        msg = cli_socket.recv(M_SIZE)
        if (len(msg)==0):
            msg={'type':'O','msg':''}
        else:
            msg = json.loads(msg.decode())
        if msg['type']=='J':
            list_name[client_list.index(cli_socket)]= msg["msg"] +"-"+ list_name[client_list.index(cli_socket)]
            print(f'Client {list_name[client_list.index(cli_socket)]} send msg: JOIN')

        for client in client_list:
            if client != cli_socket:
                if msg['type']=='J':                    
                    client.send(f'\t<<<{msg["msg"]}>>> JOIN'.encode())
                elif msg['type']=='N':
                    if msg["msg"]=='':
                        continue
                    client.send(f'<{datetime.now().strftime("%H:%M")}>[{list_name[client_list.index(cli_socket)]}]:{msg["msg"]}'.encode())
                elif msg['type']=='O':
                    client.send(f'\t <<<{list_name[client_list.index(cli_socket)]}>>> OUT'.encode())

        if msg['type']=='O':                            
            print(f'Client {list_name[client_list.index(cli_socket)]} OUT')
            list_name.pop(client_list.index(cli_socket))
            client_list.remove(cli_socket)
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