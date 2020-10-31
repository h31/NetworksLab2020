import socket
import threading

host = "127.0.0.1"  # ip сервера (localhost)
port = 44444  # порт

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))

server.listen()

clients = []  # адреса (!) подключенных клиентов
nicknames = []

# Функция для отправки сообщения подключенному пользователю
def broadcast(message):
    for client in clients:
        client.send(message)

def handle(client):
    while True:
        try:
            message = client.recv(1024)
            broadcast(message)
        except:
            clientIndex = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[clientIndex]
            nicknames.remove(nickname)
            broadcast(f"[{nickname}] left the chat".encode("ascii"))
            break

def receive():
    while True:
        client, addres = server.accept()
        print(f"Connected with {str(addres)}")

        client.send("Nickname:".encode("ascii"))
        nickname = client.recv(1024).decode("ascii")
        nicknames.append(nickname)
        clients.append(client)

        print(f"Nickname of the client is {nickname}")
        broadcast(f"[{nickname}] joined the chat".encode("ascii"))
        client.send("Connected to the server".encode("ascii"))

        thread = threading.Thread(target = handle, args = (client, ))
        thread.start()

print("---Server Started---")
receive()

#currentTime = time.strftime("%Y-%m-%d-%H.%M.%S", time.localtime())
# print("[" + addr[0] + "]=[" + str(addr[1]) + "]=[" + currentTime + "]/", end="")
