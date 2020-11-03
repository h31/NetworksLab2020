import socket
import threading
import time
from datetime import datetime

BUFSIZE = 256
TIMEZONE = time.timezone

host = "127.0.0.1"  # ip сервера (localhost)
# host = "0.0.0.0"  # ip сервера (localhost)
port = 44444  # порт

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))

server.listen()

serverNickname = "Server"

clients = []  # адреса (!) подключенных клиентов
nicknames = []

def getData(time, nickname, message):
    data = f"{time}\0{nickname}\0{message}".encode("utf-8")
    return f"{len(data):<{BUFSIZE}}".encode("utf-8") + data

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
    while True:
        try:
            messageLength = int(client.recv(BUFSIZE).decode("utf-8"))
            rawData = client.recv(BUFSIZE)
            currentLength = len(rawData)
            while messageLength != currentLength:
                rawData += client.recv(BUFSIZE)
                currentLength = len(rawData)
            data = rawData.decode("utf-8")
            receiptTime = serverTime()
            userTime, nickname, message = data.split("\0")
            newData = getData(receiptTime, nickname, message)
            printLog(serverTimeFormat(receiptTime), f"[{addres[0]}:{str(addres[1])}]/[{nickname}] -> {message}")
            broadcast(client, newData)
        except:
            currentTime = serverTime()
            clientIndex = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[clientIndex]
            nicknames.remove(nickname)
            leftmsg = f"[{nickname}] left the chat"
            printLog(serverTimeFormat(currentTime), leftmsg)
            data = getData(currentTime, serverNickname, leftmsg)
            broadcast(client, data)
            break

# Функция для обработки подключения пользователей к серверу
def receive():
    while True:
        client, addres = server.accept()
        printLog(serverTimeFormat(serverTime()), f"Connected with {str(addres)}")

        data = getData(serverTime(), serverNickname, "\1GET_NICKNAME")
        client.send(data)
        nickname = client.recv(1024).decode("utf-8").split("\0")[1]
        nicknames.append(nickname)
        clients.append(client)

        currentTime = serverTime()
        joinmsg = f"[{nickname}] joined the chat"
        printLog(serverTimeFormat(currentTime), joinmsg)
        data = getData(currentTime, serverNickname, joinmsg)
        client.send(data)
        broadcast(client, data)

        thread = threading.Thread(target = handle, args = (client, addres))
        thread.start()

print("---Server Started---")
receive()
