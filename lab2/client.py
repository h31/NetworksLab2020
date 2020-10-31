import socket
import threading as th
from datetime import datetime
import sys

HEADER = 10
ENCODE = 'utf-8'

AUTHORIZATION = '1'
DISCONNECT = '2'
SEND = '3'
CHANGE_NICK = '4'

def setup_client():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"Choose where the server deployed:"
    f"\n1 - Enter manually"
    f"\n2 - localhost(127.0.0.1)"
    f"\n3 - {hostname}({ip_address})")
    while True:
        mode = input()
        if (mode != '1') & (mode != '2') & (mode != '3'): 
            print("Bad input")
            continue
        elif mode == '1':
            while True:
                ip_address = input("Format - x.x.x.x: ")
                try:
                    socket.inet_aton(ip_address)
                    break
                except socket.error:
                    print("Bad input")
                    continue
            break
        elif mode == '2':
                ip_address = 'localhost'
                break
        else:
            break

    port = int(input("Enter port(1024 - 65535):"))
    if(1024 > port):
        print("Warning! Reserved port")
        port = 1024
    elif(port > 65535):
        print("Warning! Out of range")
        port = 65535

    client(ip_address, port)

def client(IP, PORT):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket.connect((IP, PORT))

    print(f"Connection with {IP}:{PORT} established.")

    while True:
        username = input("Enter username:")
        if username != '':
            client_socket.send(f'{len(AUTHORIZATION):<{HEADER}}'.encode(ENCODE) + AUTHORIZATION.encode(ENCODE))
            client_socket.send(f'{len(username.encode(ENCODE)):<{HEADER}}'.encode(ENCODE) + username.encode(ENCODE))
            print(f"Authorization complete.")
            break

    th.Thread(target = recv_handler, args = (client_socket, )).start()
    th.Thread(target = send_handler, args = (client_socket, )).start()

def read_package(client_socket):
    header = client_socket.recv(HEADER)
    if not header:
        return False

    while(len(header) != HEADER):
        header_tmp = client_socket.recv(HEADER - len(header))
        header += header_tmp
    
    data_len = int(header.decode(ENCODE))

    data = client_socket.recv(data_len)
    if not data:
        return False

    while(len(data) != data_len):
        data_tmp = client_socket.recv(HEADER - len(data))
        data += data_tmp

    return data.decode(ENCODE)

def convert_time(_time):
    return datetime.fromtimestamp(float(_time)).strftime("%H:%M:%S")

def recv_handler(client_socket):
    while True:      
        try:
            username = read_package(client_socket)
            message = read_package(client_socket)
            send_time = read_package(client_socket)
            print(f"<{convert_time(send_time)}> [{username}]: {message}")
        except OSError:
            print(f"Connection was closed.")
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
            return

def send_handler(client_socket):
    print(f"\nAvailable commands:\n"
    f"!disconnect - close connection and leave chat\n"
    f"!change - change current nickaname\n")
    while True:
        try:
            message = input()

            if message == '!disconnect'.encode(ENCODE):
                client_socket.send(f'{len(DISCONNECT):<{HEADER}}'.encode(ENCODE) + DISCONNECT.encode(ENCODE))
                client_socket.shutdown(socket.SHUT_RDWR)
                client_socket.close()
                sys.exit()
            elif message == '!change'.encode(ENCODE):
                username = input("Enter new username:")
                client_socket.send(f'{len(CHANGE_NICK):<{HEADER}}'.encode(ENCODE) + CHANGE_NICK.encode(ENCODE))
                client_socket.send(f"{len(username.encode(ENCODE)):<{HEADER}}".encode(ENCODE) + username.encode(ENCODE))
            elif message:
                client_socket.send(f'{len(SEND):<{HEADER}}'.encode(ENCODE) + SEND.encode(ENCODE))
                client_socket.send(f"{len(message.encode(ENCODE)):<{HEADER}}".encode(ENCODE) + message.encode(ENCODE))
        except OSError:
            print(f"Connection was closed.")
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
            return
            
setup_client()