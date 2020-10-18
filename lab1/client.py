import socket
import sys
import threading
import time
from datetime import datetime

import tzlocal as tzlocal

from tzlocal import get_localzone

import pytz as pytz

message_time = 0
SERVER_MASSAGE = "SERVER DEAD"

HEADER = 64
PORT = 8080
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)


def read_listen(check):
    while True:
        if check == False:
            print('Enter any key to exit')
            send_server(SERVER_MASSAGE)
            read_all_world(False)
            client.shutdown(socket.SHUT_WR)
            client.close()
            break
        else:
            msg = input()
            while msg.find(']: ') != -1 or msg.find('[ ') != -1:
                msg = input("Don't use '[ ' or ']: repeat please!' \n"
                                   'Input massage:')
            if msg == DISCONNECT_MESSAGE:
                print('you are disconnected from the server')
                send_server(DISCONNECT_MESSAGE)
                read_all_world(False)
                client.shutdown(socket.SHUT_WR)
                client.close()
                break
            else:
                hour = datetime.now().hour
                minute = datetime.now().minute
                nnn = - time.timezone / 3600
                strin_time = str(hour) + ':' + str(minute) + ' ' + str(nnn) + ' '
                send_server(strin_time + msg)


def send_server(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    try:
        client.send(send_length)
        client.send(message)
    except:
        sys.exit(0)


def time_set(h, m):
    return h + ':' + m

def name_set(name):
    listName = name.split(' ]:')
    name = listName[0]
    kok = name.split('[ ')
    return kok[1]

def read_all_world(check):
    while check:
        try:
            data = client.recv(2048).decode(FORMAT)
            if data == SERVER_MASSAGE:
                print(data)
                read_listen(False)
            else:
                work_time = data.split(' ]: ')
                ooo = work_time[-1].split()
                current_time = ooo[0]
                ooo.pop(0)
                time_zone = ooo[0]
                ooo.pop(0)
                client_timezone = - time.timezone / 3600
                if time_zone != str(client_timezone):
                    number1 = client_timezone - float(time_zone)
                    hour, minute = current_time.split(':')[0], current_time.split(':')[1]
                    df = int(number1)
                    hour = int(hour) + df
                    if hour > 23:
                        hour = hour - 24
                        current_time = time_set(hour, minute)
                        current_name = name_set(data)
                        current_msg = ' '.join(ooo)
                        print(current_time + ' [ ' + current_name + ' ]:' + current_msg)
                    elif hour < 0:
                        hour = 24 + hour
                        current_time = time_set(hour, minute)
                        current_name = name_set(data)
                        current_msg = ' '.join(ooo)
                        print(current_time + ' [ ' + current_name + ' ]:' + current_msg)
                    else:
                        current_time = time_set(str(hour), minute)
                        current_name = name_set(data)
                        current_msg = ' '.join(ooo)
                        print(current_time + ' [ ' + current_name + ' ]:' + current_msg)
                else:
                    current_name = name_set(data)
                    current_msg = ' '.join(ooo)
                    print(current_time + ' [ ' + current_name + ' ]:' + current_msg)


        except:
            sys.exit(0)


clientText = input("Don't use '[ ' or ']: ' in the name or massage \n"
                   'Input your name:')
while clientText.find(']: ') != -1 or clientText.find('[ ') != -1:
    clientText = input("Don't use '[ ' or ']: repeat please!' \n"
                       'Input your name:')
send_server(clientText)
potok = threading.Thread(target=read_all_world, args=(True,))
potok.start()

read_listen(True)
