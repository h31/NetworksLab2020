import socket
import threading
import time

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
    return f"{time}\0{nickname}\0{message}".encode("utf-8")

def serverTime():
    return time.strftime("%Y-%m-%d-%H.%M.%S", time.localtime())

def printLog(message):
    printLogTime(serverTime(), message)

def printLogTime(time, message):
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
            data = client.recv(1024).decode("utf-8")
            receiptTime = serverTime()
            userTime, nickname, message = data.split("\0")
            newData = getData(receiptTime, nickname, message)
            printLogTime(receiptTime, f"[{addres[0]}:{str(addres[1])}]/[{nickname}] -> {message}")
            broadcast(client, newData)
        except:
            currentTime = serverTime()
            clientIndex = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[clientIndex]
            nicknames.remove(nickname)
            leftmsg = f"[{nickname}] left the chat"
            printLogTime(currentTime, leftmsg)
            data = getData(currentTime, serverNickname, leftmsg)
            broadcast(client, data)
            break

# Функция для обработки подключения пользователей к серверу
def receive():
    while True:
        client, addres = server.accept()
        printLog(f"Connected with {str(addres)}")

        data = getData(serverTime(), serverNickname, "GET_NICKNAME\1")
        client.send(data)
        nickname = client.recv(1024).decode("utf-8").split("\0")[1]
        nicknames.append(nickname)
        clients.append(client)

        currentTime = serverTime()
        joinmsg = f"[{nickname}] joined the chat"
        printLogTime(currentTime, joinmsg)
        data = getData(currentTime, serverNickname, joinmsg)
        client.send(data)
        broadcast(client, data)

        thread = threading.Thread(target = handle, args = (client, addres))
        thread.start()

print("---Server Started---")
receive()
