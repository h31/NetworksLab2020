import socket
import threading
import time
import sys

serverIP = sys.argv[1]
port = 44444

nickname = input("Nickname: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((serverIP, port))

def receive():
    while True:
        try:
            message = client.recv(1024).decode("utf-8")
            if message == "NICK":
                client.send(nickname.encode("utf-8"))
            else:
                currentTime = time.strftime("%Y-%m-%d-%H.%M.%S", time.localtime())
                print(f"<{currentTime}> {message}")
        except:
            print("Error")
            client.close()
            break

def write():
    while True:
        message = f'[{nickname}]: {input("")}'
        client.send(message.encode("utf-8"))

receiveThread = threading.Thread(target = receive)
receiveThread.start()

writeThread = threading.Thread(target = write)
writeThread.start()















