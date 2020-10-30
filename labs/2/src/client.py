import socket
import threading
import sys
from datetime import datetime
import time
import utilz

NEWMSGSTYLE = '<{time}> [{name}]: {msg}'
TIMEFORMAT = '%H:%M'

flag = True


def send_msg(cs, name):
    global flag
    while flag:
        try:
            msg = input()
        except:
            continue

        if not msg:
            continue

        if len(msg.encode()) > utilz.MAX_SIZE:
            print(f'Encoded message size exceeded: {len(msg)} > {utilz.MAX_SIZE}')
            print('Message have not been send')
            continue

        if msg[0] == '\\':
            if msg[1] == 'q':
                send_exit(cs, name)
                cs.close()
                break
            continue

        try:
            cs.send(utilz.msg_content(1, name, msg))
        except:
            flag = False
            break


def ping(cs):
    global flag
    while flag:
        try:
            cs.send(utilz.msg_content(4))
            time.sleep(5)
        except:
            print('Server closed connection')
            flag = False
            break


def recv_msg(cs, name):
    global flag
    while flag:
        try:
            req = utilz._recv_msg(cs, utilz.HEADER_SIZE)

            if not req:
                continue

            header = utilz.Header(req)
            body = {
                'type': header.type,
            }
            for _type, size in header.type_to_len:
                data = utilz._recv_msg(cs, size)
                body[_type] = data

            if body['type'] == 4:
                continue

            print_msg(body)
        except:
            send_exit(cs, name)
            cs.close()
            break


def send_exit(cs, name):
    try:
        cs.send(utilz.msg_content(2, name))
    except:
        pass

    flag = False


def print_msg(data):
    if data['type'] == utilz.Type.MESSAGE:
        print(NEWMSGSTYLE.format(time=timeformat(float(data['time'])),
                                 name=data['name'],
                                 msg=data['msg']))
    else:
        print(data['msg'].format(name=data['name']))


def timeformat(timestamp):
    return datetime.fromtimestamp(timestamp).strftime(TIMEFORMAT)


def client():
    cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        cs.connect((utilz.HOST, utilz.PORT))
    except:
        cs.close()
        print(f'Can not connect to the server: {utilz.HOST}:{utilz.PORT}')
        sys.exit()

    name = input('Your nickname: ')
    try:
        cs.send(utilz.msg_content(0, name))
    except:
        cs.close()
        print('Server error')
        sys.exit()

    threading.Thread(target=send_msg, args=(cs, name)).start()
    threading.Thread(target=recv_msg, args=(cs, name)).start()
    threading.Thread(target=ping, args=(cs, )).start()


client()
