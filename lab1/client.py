import socket
import threading
import time
from datetime import datetime

BUFSIZE = 256
TIMEZONE = time.timezone

serverIP = "127.0.0.1"
# serverIP = "51.15.130.137"
port = 44444

clientNickname = input("Nickname: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((serverIP, port))

def clientTime():
    return datetime.timestamp(datetime.now()) + TIMEZONE

def getData(time, nickname, message):
    data = f"{time}\0{nickname}\0{message}".encode("utf-8")
    return f"{len(data):<{BUFSIZE}}".encode("utf-8") + data

# Функция для обработки информации, приходящей с сервера
def receive():
    while True:
        try:
            messageLength = int(client.recv(BUFSIZE).decode("utf-8"))
            rawData = client.recv(BUFSIZE)
            currentLength = len(rawData)
            while messageLength != currentLength:
                rawData += client.recv(BUFSIZE)
                currentLength = len(rawData)
            data = rawData.decode("utf-8")
            serverTime, nickname, message = data.split("\0")
            if nickname == "Server" and message == "\1GET_NICKNAME":
                data = getData(clientTime(), clientNickname, "\1POST_NICKNAME")
                client.send(data)
            else:
                # Прибавляем к времени наш часовой пояс

                messageTime = datetime.strftime(datetime.fromtimestamp(float(serverTime) - TIMEZONE), "%Y-%m-%d-%H.%M.%S")
                print(f"<{messageTime}> [{nickname}] {message}")
        except:
            print("Error")
            client.close()
            break

# Функция для отправки сообщений на сервер
def write():
    while True:
        message = input("")
        data = getData(clientTime(), clientNickname, message)
        client.send(data)

receiveThread = threading.Thread(target = receive)
receiveThread.start()

writeThread = threading.Thread(target = write)
writeThread.start()

# Для обеспечения правильного поведения консоли (при закрытии)
def on_exit(sig, func=None):
    print("exit handler")
    time.sleep(10)  # so you can see the message before program exits
