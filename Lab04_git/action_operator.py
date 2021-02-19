import json
import sys
from math import ceil

from server import BLOCK_SIZE
from encrypt import encrypt_password
from database_handler import add_to_database, get_from_database, delete_from_database, get_total_amount
from datetime import datetime

date_format = '%Y-%m-%d %H:%M:%S.%f'


def authenticate(user, conn):
    data = conn.recv(BLOCK_SIZE).decode("utf-8")
    data = json.loads(data)
    password = data.get("password", None)

    if password == -1:
        print(f'Authenticated user {user} as USER.')
        return False
    else:
        password = encrypt_password(password)
        correct_password = get_from_database({"type": "password"})['password']

        if password == correct_password:
            accept = {"type": "auth", "password": 1}
            conn.send(bytes(json.dumps(accept), encoding="utf-8"))
            print(f'Authenticated user {user} as ADMIN.')
            return True
        else:
            accept = {"type": "auth", "password": -1}
            conn.send(bytes(json.dumps(accept), encoding="utf-8"))
            print(f'Authenticated user {user} as USER. (Wrong admin password)')
            return False


def park(number, conn, address):
    if get_from_database({"_id": number}) is None:
        accept = {"type": "accept"}
        conn.send(bytes(json.dumps(accept), encoding="utf-8"))

        start_time = datetime.now().strftime(date_format)
        db = {"_id": number, "time": start_time}
        add_to_database(db)

        print(f'Parked car {number} successfully.')
        add_to_database(
            {"type": "log", "date": datetime.now(),
             "text": f"Parked car {number} successfully from user {address}"})

    else:
        error = {"type": "error", "code": 1}  # car is already parked
        conn.send(bytes(json.dumps(error), encoding="utf-8"))
        add_to_database(
            {"type": "log", "date": datetime.now(), "text": f"Sent error 1 to user {address}"})


def unpark(number, conn, address):
    if get_from_database({"_id": number}) is not None:
        finish_time = datetime.now().strftime(date_format)

        start_time = get_from_database({"_id": number}).get("time", None)
        diff = datetime.strptime(finish_time, date_format) - datetime.strptime(start_time,
                                                                               date_format)
        amount = ceil(diff.seconds / 3600) * 100  # 100 = price per hour

        checkout = {"type": "checkout", "amount": amount}
        conn.send(bytes(json.dumps(checkout), encoding="utf-8"))

        delete_from_database({"_id": number})

        db = {"type": "history", "number": number, "date": finish_time, "amount": amount}
        add_to_database(db)

        add_to_database(
            {"type": "log", "date": datetime.now(),
             "text": f"UNparked car {number} successfully from user {address}"})

    else:
        error = {"type": "error", "code": 2}  # car is not parked yet
        conn.send(bytes(json.dumps(error), encoding="utf-8"))
        add_to_database(
            {"type": "log", "date": datetime.now(), "text": f"Sent error 2 to user {address}"})


def get_big_data(type, conn):
    data = get_from_database({"type": type}, multiple=True)
    data = json.dumps(data, default=str)
    data = bytes(data, encoding="utf-8")

    data_size_bytes = sys.getsizeof(data)

    ack_data = {"type": "size", "size": data_size_bytes}
    conn.send(bytes(json.dumps(ack_data), encoding="utf-8"))
    conn.send(data)


def get_total(conn):
    total_amount = get_total_amount()
    conn.send(bytes(json.dumps(total_amount[0]), encoding="utf-8"))
