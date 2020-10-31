import socket
import threading
import time

host = "0.0.0.0"  # ip сервера (localhost)
port = 44444  # порт

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))

server.listen()

clients = []  # адреса (!) подключенных клиентов
nicknames = []

# Функция для отправки сообщения подключенному пользователю
def broadcast(muteClient, message):
    for client in clients:
        if client != muteClient:
            client.send(message)

def handle(client, addres):
    while True:
        try:
            message = client.recv(1024)
            currentTime = time.strftime("%Y-%m-%d-%H.%M.%S", time.localtime())
            print(f"[{addres[0]}:{str(addres[1])}]/[{currentTime}]/", end="")
            print(message.decode("utf-8"))
            broadcast(client, message)
        except:
            clientIndex = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[clientIndex]
            nicknames.remove(nickname)
            currentTime = time.strftime("%Y-%m-%d-%H.%M.%S", time.localtime())
            print(f"[{currentTime}]/[log]: [{nickname}] left the chat")
            broadcast(client, f"[{nickname}] left the chat".encode("utf-8"))
            break

def receive():
    while True:
        client, addres = server.accept()
        currentTime = time.strftime("%Y-%m-%d-%H.%M.%S", time.localtime())
        print(f"[{currentTime}]/[log]: Connected with {str(addres)}")

        client.send("NICK".encode("utf-8"))
        nickname = client.recv(1024).decode("utf-8")
        nicknames.append(nickname)
        clients.append(client)

        currentTime = time.strftime("%Y-%m-%d-%H.%M.%S", time.localtime())
        print(f"[{currentTime}]/[log]: {nickname} joined the chat")
        broadcast(client, f"[Server]: [{nickname}] joined the chat".encode("utf-8"))
        client.send("[Server]: Connected to the server".encode("utf-8"))

        thread = threading.Thread(target = handle, args = (client, addres))
        thread.start()

print("---Server Started---")
receive()

#currentTime = time.strftime("%Y-%m-%d-%H.%M.%S", time.localtime())
# print("[" + addr[0] + "]=[" + str(addr[1]) + "]=[" + currentTime + "]/", end="")
