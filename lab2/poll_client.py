import socket
import threading
import sys
import datetime
import time
from datetime import datetime

SERVER = "51.15.130.137"
#SERVER = socket.gethostbyname(socket.gethostname())

FORMAT = 'utf-8'
PORT = 1339
HEADER = 64
CHECK = True
ADDR = (SERVER, PORT)
clientText = input('Input your name:')

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

name = clientText.encode(FORMAT)
username_msg = f"{len(name):<{HEADER}}".encode(FORMAT) + name
client.send(username_msg)

def time_set(h, m):
    return h + ':' + m

def read_listen(msg):
    work_time = msg[0].split(' ')
    client_timezone = - time.timezone / 3600
    if work_time[1] != str(client_timezone):
        number1 = client_timezone - float(work_time[1])
        hour, minute = work_time[0].split(':')
        df = int(number1)
        hour = int(hour) + df
        if hour > 23:
            hour = hour - 24
            current_time = time_set(str(hour), minute)
            current_name = msg[1]
            current_msg = msg[2]
            print(current_time + ' [ ' + current_name + ' ]:' + current_msg)
        elif hour < 0:
            hour = 24 + hour
            current_time = time_set(str(hour), minute)
            current_name = msg[1]
            current_msg = msg[2]
            print(current_time + ' [ ' + current_name + ' ]:' + current_msg)
        else:
            current_time = time_set(str(hour), minute)
            current_name = msg[1]
            current_msg = msg[2]
            print(current_time + ' [ ' + current_name + ' ]: ' + current_msg)
    else:
        current_name = msg[1]
        current_msg = msg[2]
        print(work_time[0] + ' [ ' + current_name + ' ]:' + current_msg)


def read_all_world():
    global CHECK
    while CHECK:
        try:
            mheader = client.recv(HEADER)
            if not len(mheader):
                print('Enter any key to exit')
                CHECK = False
                sys.exit(0)

            msg_lenthg = int(mheader.decode(FORMAT))
            msg = client.recv(msg_lenthg)
            nnn = msg_lenthg-len(msg)
            while nnn!= 0:
                msg += client.recv(msg_lenthg)
                nnn = msg_lenthg-len(msg)

            msg = [m.decode(FORMAT) for m in msg.split(b'\0')]
            if len(msg) == 1:
                print(msg[0])
            else:
                msg[0] = msg[0]
                read_listen(msg)
        except:
            CHECK = False
            sys.exit(0)


def message_for_sending(message):
    hour = datetime.now().hour
    minute = datetime.now().minute
    nnn = - time.timezone / 3600

    timeline = (str(hour) + ':' + str(minute) + ' ' + str(nnn)).encode(FORMAT)
    usr = clientText.encode(FORMAT)
    msg = message.encode(FORMAT)
    return b'\0'.join([timeline, usr, msg])


def send_server():
    potok = threading.Thread(target=read_all_world)
    potok.start()
    while CHECK:
        try:
            mes = input()
            if mes and CHECK:
                msg = message_for_sending(mes)
                msg = f'{len(msg):<{HEADER}}'.encode(FORMAT) + msg
                client.send(msg)
        except:
            sys.exit(0)


if __name__ == '__main__':
    send_server()
