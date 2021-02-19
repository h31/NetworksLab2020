import json
import socket
from datetime import datetime
from threading import Thread

import action_operator
from database_handler import add_to_database

HOST = '127.0.0.1'
PORT = 8080
BLOCK_SIZE = 1024
PRICE_PER_HOUR = 100


def init_server():
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print('waiting for connection...')
    add_to_database({"type": "log", "date": datetime.now(), "text": f"Server started"})
    Thread(target=connect_users).start()


def connect_users():
    global conn

    while True:
        conn, address = server_socket.accept()
        print('connected:', address)
        add_to_database({"type": "log", "date": datetime.now(), "text": f"Connected user{address}"})

        Thread(target=handle_connected_user, args=(conn, address,)).start()


def handle_connected_user(conn, address):
    is_admin = action_operator.authenticate(address, conn)

    try:
        while True:
            data = conn.recv(BLOCK_SIZE).decode("utf-8")
            if not data:
                break

            data = json.loads(data)
            action = data.get("type", None)
            add_to_database({"type": "log", "date": datetime.now(), "text": f"Got action {action} from user {address}"})

            if action == "park":
                car_number = data.get("number", None)
                action_operator.park(car_number, conn, address)

            elif action == "unpark":
                car_number = data.get("number", None)
                action_operator.unpark(car_number, conn, address)

            elif action == "history" and is_admin:
                action_operator.get_big_data(action, conn)

            elif action == "log" and is_admin:
                action_operator.get_big_data(action, conn)

            elif action == "total" and is_admin:
                action_operator.get_total(conn)

            elif action == "exit":
                print(f"User {address} disconnected.")
                return

    except ConnectionResetError:
        print("User disconnected")


if __name__ == '__main__':
    init_server()
