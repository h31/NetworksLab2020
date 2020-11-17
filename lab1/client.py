import socket
import threading
import time
from datetime import datetime

HEADER = 10
CLIENT_WORKING = True
SERVER_IP = "127.0.0.1"
# SERVER_IP = "51.15.130.137"
SERVER_PORT = 44450

clientNickname = input("Nickname: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect((SERVER_IP, SERVER_PORT))
except ConnectionRefusedError:
    print(f"Server ({SERVER_IP}:{SERVER_PORT}) is not available")
    exit(0)

def clientTime():
    return datetime.timestamp(datetime.now())

def getData(time, nickname, message):
    data = f"{time}\0{nickname}\0{message}".encode("utf-8")
    return f"{len(data):<{HEADER}}".encode("utf-8") + data

# Функция для обработки информации, приходящей с сервера
def receive():
    global CLIENT_WORKING
    data = getData(clientTime(), clientNickname, "POST_NICKNAME")
    client.send(data)
    while CLIENT_WORKING:
        try:
            messageLength = int(client.recv(HEADER).decode("utf-8"))
            rawData = client.recv(messageLength)
            currentLength = len(rawData)
            while messageLength != currentLength:
                rawData += client.recv(messageLength)
                currentLength = len(rawData)
            data = rawData.decode("utf-8")
            serverTime, nickname, message = data.split("\0")

            # Прибавляем к времени наш часовой пояс
            messageTime = datetime.strftime(datetime.fromtimestamp(float(serverTime)), "%Y-%m-%d-%H.%M.%S")
            print(f"<{messageTime}> [{nickname}] {message}")
        except ConnectionResetError or KeyboardInterrupt:
            print("Error")
            client.close()
            break
        except ValueError:
            CLIENT_WORKING = False
            print("Server close connection")
            client.close()
            break

# Функция для отправки сообщений на сервер
def write():
    global CLIENT_WORKING
    while CLIENT_WORKING:
        message = input("")
        data = getData(clientTime(), clientNickname, message)
        if CLIENT_WORKING:
            client.send(data)
        else:
            break

receiveThread = threading.Thread(target = receive)
receiveThread.start()

writeThread = threading.Thread(target = write)
writeThread.start()

# Для обеспечения правильного поведения консоли (при закрытии)
def on_exit(sig, func=None):
    print("exit handler")
    time.sleep(10)  # so you can see the message before program exits
