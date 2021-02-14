import json
import socket
from threading import Thread
from Encrypt import encryptPassword

HOST = '127.0.0.1'
PORT = 8080
BLOCK_SIZE = 1024

operations = ['1', '2', '3']


def main():
    def initClient():
        global clientSocket
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            clientSocket.connect((HOST, PORT))
            print("Connected successfully")

            handleOperations(authenticate())

        except ConnectionRefusedError:
            print("The server is unreachable")

    def authenticate():
        print("Enter admin password, otherwise press ENTER:")
        data = input()
        if (data == ''):
            authData = {"type": "auth", "password": -1}
            clientSocket.send(bytes(json.dumps(authData), encoding="utf-8"))
            print("You are now entering USER mode")
            return False
        else:
            data = encryptPassword(data)
            authData = {"type": "auth", "password": data}
            clientSocket.send(bytes(json.dumps(authData), encoding="utf-8"))

            # expecting {auth, 1 if success OR auth, -1 if DENY}

            data = clientSocket.recv(BLOCK_SIZE).decode('utf-8')
            data = json.loads(data)
            flag = data.get("password", None)

            if (flag == 1):
                print("You are now entering ADMIN mode")
                return True
            else:
                print("Wrong admin password. Entering user mode.")
                return False

    def handleOperations(isAdmin):
        printMenu(isAdmin)

        while True:
            operation = input()

            if not operation:
                break

            if operation not in operations:
                print("Wrong input")
                continue

            if (operation == '1'):
                if (isAdmin):
                    operateAdmin("history")
                else:
                    operateCar("park")
            elif (operation == '2'):
                if (isAdmin):
                    operateAdmin("log")
                else:
                    operateCar("unpark")

    def operateCar(type):
        print("Enter car number:")
        carNumber = input()
        data = {"type": type, "number": carNumber}
        clientSocket.send(bytes(json.dumps(data), encoding="utf-8"))

        data = clientSocket.recv(BLOCK_SIZE).decode('utf-8')
        data = json.loads(data)

        type = data.get("type", None)

        if (type == 'error'):
            print(f"Error: . Check car number you typed: {carNumber}")
        elif (type == 'checkout'):
            amount = data.get("amount", None)
            print(f"You finished your parking. Amount to pay: {amount}")
        else:
            print(f'Car {carNumber} parked successfully.')

    def operateAdmin(type):
        data = {"type": type}
        clientSocket.send(bytes(json.dumps(data), encoding="utf-8"))

        data = clientSocket.recv(BLOCK_SIZE).decode('utf-8')
        print(data)

    def printMenu(isAdmin):
        if (isAdmin):
            print("1 - get history\n"
                  "2 - get log\n"
                  "3 - exit\n")
        else:
            print("1 - start parking\n"
                  "2 - finish parking\n"
                  "3 - exit\n")

    Thread(target=initClient).start()


if __name__ == '__main__':
    main()
