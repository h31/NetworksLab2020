import json
import socket
from threading import Thread
from datetime import datetime
from math import ceil
from DatabaseHandler import addToDB, getFromDB
from Encrypt import encryptPassword

HOST = '127.0.0.1'
PORT = 8080
BLOCK_SIZE = 1024
PRICE_PER_HOUR = 100

parkedCarsNumbers = dict.fromkeys(['', ])


def main():
    def initServer():
        global serverSocket
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind((HOST, PORT))
        serverSocket.listen(5)
        print('waiting for connection...')
        addToDB({"type": "log", "date": datetime.now(), "text": f"Server started"})
        Thread(target=connectUsers).start()

    def connectUsers():
        global conn

        while True:
            conn, address = serverSocket.accept()
            print('connected:', address)
            addToDB({"type": "log", "date": datetime.now(), "text": f"Connected user{address}"})

            Thread(target=handleConnectedUser, args=(conn, address,)).start()

    def authenticate(user):
        data = conn.recv(BLOCK_SIZE).decode("utf-8")
        data = json.loads(data)
        password = data.get("password", None)

        if (password == -1):
            print(f'Authenticated user {user} as USER.')
            return False
        else:
            password = encryptPassword(password)
            correctPassword = getFromDB({"type": "password"})
            correctPassword = correctPassword['password']

            if (password == correctPassword):
                accept = {"type": "auth", "password": 1}
                conn.send(bytes(json.dumps(accept), encoding="utf-8"))
                print(f'Authenticated user {user} as ADMIN.')
                return True
            else:
                accept = {"type": "auth", "password": -1}
                conn.send(bytes(json.dumps(accept), encoding="utf-8"))
                print(f'Authenticated user {user} as USER. (Wrong admin password)')
                return False

    def handleConnectedUser(conn, address):
        datetimeFormat = '%Y-%m-%d %H:%M:%S.%f'
        isAdmin = authenticate(address)
        try:
            while True:
                data = conn.recv(BLOCK_SIZE).decode("utf-8")
                if not data:
                    break

                data = json.loads(data)
                action = data.get("type", None)
                addToDB({"type": "log", "date": datetime.now(), "text": f"Got action {action} from user {address}"})

                if (action == "park"):
                    carNumber = data.get("number", None)

                    if (carNumber not in parkedCarsNumbers):
                        accept = {"type": "accept"}
                        conn.send(bytes(json.dumps(accept), encoding="utf-8"))

                        parkTime = datetime.now().strftime(datetimeFormat)
                        parkedCarsNumbers[carNumber] = parkTime

                        print(f'Parked car {carNumber} successfully.')
                        addToDB(
                            {"type": "log", "date": datetime.now(),
                             "text": f"Parked car {carNumber} successfully from user {address}"})

                    else:
                        error = {"type": "error", "code": 1}  # car is already parked
                        conn.send(bytes(json.dumps(error), encoding="utf-8"))
                        addToDB(
                            {"type": "log", "date": datetime.now(), "text": f"Sent error 1 to user {address}"})

                elif (action == "unpark"):
                    carNumber = data.get("number", None)

                    if (carNumber in parkedCarsNumbers):
                        unparkTime = datetime.now().strftime(datetimeFormat)
                        parkTime = parkedCarsNumbers[carNumber]

                        diff = datetime.strptime(unparkTime, datetimeFormat) - datetime.strptime(parkTime,
                                                                                                 datetimeFormat)
                        amountToPay = ceil(diff.seconds / 3600) * PRICE_PER_HOUR

                        checkout = {"type": "checkout", "amount": amountToPay}
                        conn.send(bytes(json.dumps(checkout), encoding="utf-8"))

                        DBinfo = {"type": "history", "number": carNumber, "date": unparkTime, "amount": amountToPay}
                        addToDB(DBinfo)

                        del parkedCarsNumbers[carNumber]

                        addToDB(
                            {"type": "log", "date": datetime.now(),
                             "text": f"UNparked car {carNumber} successfully from user {address}"})

                    else:
                        error = {"type": "error", "code": 2}  # car is not parked yet
                        conn.send(bytes(json.dumps(error), encoding="utf-8"))
                        addToDB(
                            {"type": "log", "date": datetime.now(), "text": f"Sent error 2 to user {address}"})

                elif (action == "history" and isAdmin):
                    history = getFromDB({"type": "history"}, multiple=True)
                    history = json.dumps(history, default=str)
                    conn.send(bytes(history[-900:], encoding="utf-8"))

                elif (action == "log" and isAdmin):
                    history = getFromDB({"type": "log"}, multiple=True)
                    history = json.dumps(history, default=str)
                    conn.send(bytes(history[-500:], encoding="utf-8"))

        except ConnectionResetError:
            print("User disconnected")

    Thread(target=initServer).start()


if __name__ == '__main__':
    main()
