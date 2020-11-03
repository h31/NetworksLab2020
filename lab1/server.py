import socket
import threading
import time
from datetime import datetime

HEADER = 10
TIMEZONE = time.timezone
SERVER_WORKING = True
# HOST = "127.0.0.1"  # ip сервера (localhost)
HOST = "0.0.0.0"
PORT = 44450  # порт
SERVER_NICKNAME = "Server"
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))

server.listen()

clients = []  # адреса (!) подключенных клиентов
nicknames = []

def getData(time, nickname, message):
    data = f"{time}\0{nickname}\0{message}".encode("utf-8")
    return f"{len(data):<{HEADER}}".encode("utf-8") + data

def serverTime():
    return datetime.timestamp(datetime.now()) + TIMEZONE

def serverTimeFormat(mytime):
    return datetime.strftime(datetime.fromtimestamp(mytime), "%Y-%m-%d-%H.%M.%S")

def printLog(time, message):
    print(f"[{time}]/[log]: {message}")

# Функция для отправки сообщения подключенным пользователям
def broadcast(muteClient, data):
    for client in clients:
        if client != muteClient:
            client.send(data)

# Функция для работы с клиентом. Получаем сообщения и обрабатываем их
def handle(client, addres):
    while SERVER_WORKING:
        try:
            messageLength = int(client.recv(HEADER).decode("utf-8"))
            rawData = client.recv(messageLength)
            currentLength = len(rawData)
            while messageLength != currentLength:
                rawData += client.recv(messageLength)
                currentLength = len(rawData)
            data = rawData.decode("utf-8")
            receiptTime = serverTime()
            userTime, nickname, message = data.split("\0")
            newData = getData(receiptTime, nickname, message)
            printLog(serverTimeFormat(receiptTime), f"[{addres[0]}:{str(addres[1])}]/[{nickname}] -> {message}")
            broadcast(client, newData)
        except ConnectionResetError:
            currentTime = serverTime()
            clientIndex = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[clientIndex]
            nicknames.remove(nickname)
            leftmsg = f"[{nickname}] left the chat"
            printLog(serverTimeFormat(currentTime), leftmsg)
            data = getData(currentTime, SERVER_NICKNAME, leftmsg)
            broadcast(client, data)
            break

# Функция для обработки подключения пользователей к серверу
def receive():
    global SERVER_WORKING
    try:
        while SERVER_WORKING:
            client, addres = server.accept()
            printLog(serverTimeFormat(serverTime()), f"Connected with {str(addres)}")

            # Получаем ник пользователя
            messageLength = int(client.recv(HEADER).decode("utf-8"))
            nickname = client.recv(messageLength).decode("utf-8").split("\0")[1]
            nicknames.append(nickname)
            clients.append(client)

            currentTime = serverTime()
            joinmsg = f"[{nickname}] joined the chat"
            printLog(serverTimeFormat(currentTime), joinmsg)
            data = getData(currentTime, SERVER_NICKNAME, joinmsg)
            client.send(data)
            broadcast(client, data)

            thread = threading.Thread(target = handle, args = (client, addres))
            thread.start()
    except KeyboardInterrupt:
        SERVER_WORKING = False
        print("---Server Stopped---")
        newData = getData(serverTime(), SERVER_NICKNAME, "Server shutdown")
        broadcast(None, newData)
        for client in clients:
            client.close()
        server.close()
        exit(0)

print("---Server Started---")
receive()
