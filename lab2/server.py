import selectors
import socket
import time
from datetime import datetime

HEADER = 10
SERVER_WORKING = True
HOST = "127.0.0.1"  # ip сервера (localhost)
# HOST = "0.0.0.0"
PORT = 44450  # порт
SERVER_NICKNAME = "Server"
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))

server.listen()
server.setblocking(False)
sel = selectors.DefaultSelector()

clients = {}  # адреса и сообщения (!) подключенных клиентов

def getData(time, nickname, message):
    data = f"{time}\0{nickname}\0{message}".encode("utf-8")
    return f"{len(data):<{HEADER}}".encode("utf-8") + data

def serverTime():
    return datetime.timestamp(datetime.now())

def serverTimeFormat(mytime):
    return datetime.strftime(datetime.fromtimestamp(mytime  + time.timezone), "%Y-%m-%d-%H.%M.%S")

def printLog(time, message):
    print(f"[{serverTimeFormat(time)}]/[log]: {message}")

# Функция для отправки сообщения подключенным пользователям
def broadcast(muteClient, data):
    for client in clients.keys():
        if client != muteClient:
            client.send(data)

# Функция для работы с клиентом. Получаем сообщения и обрабатываем их
def handle(client):
    if SERVER_WORKING:
        try:
            # Асинхронная обработка получения сообщений от пользователей (решение проблемы BlockingIOError)
            if client not in clients.keys():
                # Получаем ник пользователя
                messageLength = int(client.recv(HEADER).decode("utf-8"))
                nickname = client.recv(messageLength).decode("utf-8").split("\0")[1]

                # Src: https://stackoverflow.com/a/16333441
                clients[client] = {}
                clients[client]['nickname'] = nickname
                clients[client]['len'] = -1
                clients[client]['msg'] = b''

                currentTime = serverTime()
                joinmsg = f"[{nickname}] joined the chat"
                printLog(currentTime, joinmsg)
                data = getData(currentTime, SERVER_NICKNAME, joinmsg)
                client.send(data)
                broadcast(client, data)
            else:
                if clients[client]['len'] == -1:
                    messageLength = int(client.recv(HEADER).decode("utf-8"))
                    clients[client]['len'] = messageLength
                else:
                    msgLength = clients[client]['len']
                    rawData = client.recv(msgLength)
                    clients[client]['msg'] += rawData
                    currentLength = len(clients[client]['msg'])
                    if currentLength == msgLength:
                        data = clients[client]['msg'].decode("utf-8")
                        clients[client]['len'] = -1
                        clients[client]['msg'] = b''

                        receiptTime = serverTime()
                        userTime, nickname, message = data.split("\0")
                        newData = getData(receiptTime, nickname, message)
                        addres = client.getsockname()
                        printLog(receiptTime, f"[{addres[0]}:{str(addres[1])}]/[{nickname}] -> {message}")
                        broadcast(client, newData)

        except ConnectionResetError:
            currentTime = serverTime()
            nickname = clients[client]['nickname']
            sel.unregister(client)
            clients.pop(client)
            client.close()
            leftmsg = f"[{nickname}] left the chat"
            printLog(currentTime, leftmsg)
            data = getData(currentTime, SERVER_NICKNAME, leftmsg)
            broadcast(client, data)

# Функция для обработки подключения пользователей к серверу
def receive(server):
    global SERVER_WORKING
    try:
        if SERVER_WORKING:
            client, addres = server.accept()
            printLog(serverTime(), f"Connected with {str(addres)}")
            client.setblocking(False)
            sel.register(fileobj=client, events=selectors.EVENT_READ, data=handle)
    except KeyboardInterrupt:
        SERVER_WORKING = False
        print("---Server Stopped---")
        newData = getData(serverTime(), SERVER_NICKNAME, "Server shutdown")
        broadcast(None, newData)
        for client in clients.keys():
            sel.unregister(client)
            client.close()
        clients.clear()
        server.close()
        exit(0)

def startServer():
    # Src: https://docs.python.org/3/library/selectors.html#examples
    sel.register(fileobj=server, events=selectors.EVENT_READ, data=receive)
    print("---Server Started---")

    while True:
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj)

startServer()
