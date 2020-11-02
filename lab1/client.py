import socket
import threading
import time

serverIP = "127.0.0.1"
# serverIP = "51.15.130.137"
port = 44444

clientNickname = input("Nickname: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((serverIP, port))

def clientTime():
    return time.strftime("%Y-%m-%d-%H.%M.%S", time.localtime())

def getData(time, nickname, message):
    return f"{time}\0{nickname}\0{message}".encode("utf-8")

# Функция для обработки информации, приходящей с сервера
def receive():
    while True:
        try:
            data = client.recv(1024).decode("utf-8")
            serverTime, nickname, message = data.split("\0")
            if nickname == "Server" and message == "GET_NICKNAME\1":
                data = getData(clientTime(), clientNickname, "POST_NICKNAME\1")
                client.send(data)
            else:
                print(f"<{serverTime}> [{nickname}] {message}")
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
