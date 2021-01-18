import socket
import threading
import os
import select
import signal
import sqlite3
import json

HOST = "0.0.0.1"
PORT = 5000
LENGTH = 4
soclist_user = []
list_user = []


SIGN_IN = "00"
SIGN_UP = "01"
BUY = "02"
CONFIRM = "03"
HISTORY_BUYER = "04"
HISTORY_SELLER = "05"
ADD_ITEMS = "06"
LIST_ITEMS = "07"
LIST_STORE = "08"
DISCONNECT = "09"
# accept user_socket

# recv and send to all user except one(who send)
def handle_data(user_s):
    db = sqlite3.connect(database="fodb.db")
    while True:
        try:
            length_d = user_s.recv(LENGTH)
        except:
            print("user disconnect")
            break
        if len(length_d) == 0:
            user_s.close()
        else:
            data = user_s.recv(int(length_d.decode("UTF-8")))
            print(data)
            data = json.loads(data.decode("UTF-8"))
            if data["type"] == SIGN_IN:
                handle_sign_in(user_s, db, data)
            elif data["type"] == SIGN_UP:
                handle_sign_up(user_s, db, data)
            elif data["type"] == BUY:
                handle_buy(user_s, db, data)
            elif data["type"] == CONFIRM:
                handle_confirm(user_s, db, data)
            elif data["type"] == HISTORY_BUYER:
                handle_history_buyer(user_s, db, data)
            elif data["type"] == HISTORY_SELLER:
                print("handle")
                handle_history_seller(user_s, db, data)
            elif data["type"] == ADD_ITEMS:
                handle_add_items(user_s, db, data)
            elif data["type"] == LIST_ITEMS:
                handle_list_items(user_s, db, data)
            elif data["type"] == LIST_STORE:
                handle_list_store(user_s, db, data)
            elif data["type"] == DISCONNECT:
                handle_disconnect(user_s, db, data)
            else:
                print("TYPE WRONG")


def handle_sign_in(user_s, db, data):
    cursor = db.execute(
        "SELECT user_name, user_password, user_role from USERS WHERE user_name = '{0}' and user_password = '{1}';".format(
            data["user"], data["password"]
        )
    )
    row = cursor.fetchall()
    if len(row) == 0:
        msg = json.dumps(
            {
                "type": SIGN_IN,
                "accepted": 0,
                "msg": "User or Password invalid",
            }
        ).encode("UTF-8")
    else:
        role = row[0][2].split("/")
        if data["role"] in role:
            msg = json.dumps(
                {
                    "type": SIGN_IN,
                    "accepted": 1,
                    "msg": "Login success",
                }
            ).encode("UTF-8")
        else:
            msg = json.dumps(
                {
                    "type": SIGN_IN,
                    "accepted": 0,
                    "msg": "Role invalid",
                }
            ).encode("UTF-8")
    send_msg(user_s, msg)


def handle_sign_up(user_s, db, data):
    print(type(data["user"]))
    cursor = db.execute(
        "SELECT user_name, user_password, user_role from USERS WHERE user_name = '{0}';".format(
            data["user"]
        )
    )
    row = cursor.fetchall()
    if len(row) == 1:
        role = row[0][2].split("/")
        if data["role"] in role:
            msg = json.dumps(
                {
                    "type": SIGN_UP,
                    "accepted": 0,
                    "msg": "User already exist",
                }
            ).encode("UTF-8")
        else:
            if row[0][1] != data["password"]:
                msg = json.dumps(
                    {
                        "type": SIGN_UP,
                        "accepted": 0,
                        "msg": "Wrong password",
                    }
                ).encode("UTF-8")
            else:
                msg = json.dumps(
                    {
                        "type": SIGN_UP,
                        "accepted": 1,
                        "msg": "role update",
                    }
                ).encode("UTF-8")
                db.execute(
                    "UPDATE USERS set user_role = 'seller/buyer' where user_name = '{0}';".format(
                        data["user"]
                    )
                )
                db.commit()
    else:
        db.execute(
            "INSERT INTO USERS (user_name,user_password, user_role) VALUES ('{0}', '{1}' , '{2}') ;".format(
                data["user"], data["password"], data["role"]
            )
        )
        db.commit()
        msg = json.dumps(
            {
                "type": SIGN_UP,
                "accepted": 1,
                "msg": "Sign up as {0} succeeded".format(data["role"]),
            }
        ).encode("UTF-8")
    send_msg(user_s, msg)


def handle_buy(user_s, db, data):
    cursor = db.execute(
        "SELECT store, area_store, items, owner from MARKET_TABLE WHERE store = '{0}'".format(
            data["store"]
        )
    )
    row = cursor.fetchall()
    if len(row) == 0:
        msg = json.dumps(
            {
                "type": BUY,
                "have_store": 0,
                "items": 0,
                "price": 0,
                "msg": "No store, please fill again",
            }
        ).encode("UTF-8")
    else:
        items_dict = dict(x.strip().split(":") for x in row[0][2].split(","))
        lack = []
        have = []
        price_items = 1000 * abs(int(row[0][1]) - int(data["area"]))
        for item in data["items"].split(","):
            if item.strip() in items_dict:
                price_items += int(items_dict[item.strip()])
                have.append(item)
            else:
                lack.append(item)

        if len(lack) == 0:
            msg = json.dumps(
                {
                    "type": BUY,
                    "have_store": 1,
                    "items": ", ".join(have),
                    "price": price_items,
                    "msg": "All items have. Do you want to buy?",
                }
            ).encode("UTF-8")
        else:
            msg = json.dumps(
                {
                    "type": BUY,
                    "have_store": 1,
                    "items": ", ".join(have),
                    "price": price_items,
                    "msg": "Do not have: {0}. Do you want to buy?".format(
                        ", ".join(lack),
                    ),
                }
            ).encode("UTF-8")
    send_msg(user_s, msg)


def handle_confirm(user_s, db, data):
    if data["accepted"] == 1:
        cursor = db.execute(
            "SELECT store,owner from MARKET_TABLE WHERE store = '{0}'".format(
                data["store"]
            )
        )
        row = cursor.fetchall()
        db.execute(
            "INSERT INTO HISTORY (buyer,items,price,seller) VALUES ('{0}', '{1}', {2}, '{3}');".format(
                data["buyer"], data["items"], data["price"], row[0][1]
            )
        )
        db.commit()
        msg = json.dumps({"type": CONFIRM, "msg": "SUCCESS"}).encode("UTF-8")
    else:
        msg = json.dumps({"type": CONFIRM, "msg": "CANCEL"}).encode("UTF-8")
    send_msg(user_s, msg)


def handle_history_buyer(user_s, db, data):
    cursor = db.execute(
        "SELECT buyer, items, price, buyer from HISTORY WHERE buyer = '{0}'".format(
            data["buyer"]
        )
    )
    history = ""
    row = cursor.fetchall()
    if len(row) == 0:
        msg = json.dumps({"type": HISTORY_BUYER, "msg": "Buy nothing"}).encode("UTF-8")
    else:
        for i in row:
            history += "Items: {0}--------Price:  {1}\n".format(i[1], i[2])
        msg = json.dumps({"type": HISTORY_BUYER, "msg": history}).encode("UTF-8")
    send_msg(user_s, msg)


def handle_history_seller(user_s, db, data):
    print("start history_seller")
    cursor = db.execute(
        "SELECT buyer, items, price, buyer from HISTORY WHERE buyer = '{0}'".format(
            data["seller"]
        )
    )
    row = cursor.fetchall()
    history = ""
    if len(row) == 0:
        msg = json.dumps({"type": HISTORY_SELLER, "msg": "Buy nothing"}).encode("UTF-8")
    else:
        for i in row:
            history += "Items: {0}--------Price:  {1}\n".format(i[1], i[2])
        msg = json.dumps({"type": HISTORY_SELLER, "msg": history}).encode("UTF-8")
    print("end hs")
    send_msg(user_s, msg)


def handle_add_items(user_s, db, data):
    print("start handle_add_items")
    cursor = db.execute(
        "SELECT store,area_store from MARKET_TABLE WHERE store = '{0}';".format(
            data["store"]
        )
    )
    row = cursor.fetchall()
    if len(row) != 0:
        msg = json.dumps(
            {"type": ADD_ITEMS, "accepted": 0, "msg": "store existed"}
        ).encode("UTF-8")
    else:
        db.execute(
            "INSERT INTO MARKET_TABLE (store,area_store, items, owner) VALUES ('{0}', {1},'{2}', '{3}') ;".format(
                data["store"], data["area_store"], data["items"], data["seller"]
            )
        )
        db.commit()
        msg = json.dumps(
            {"type": ADD_ITEMS, "accepted": 1, "msg": "add_success"}
        ).encode("UTF-8")
    send_msg(user_s, msg)


def handle_list_items(user_s, db, data):
    cursor = db.execute(
        "SELECT items from MARKET_TABLE WHERE store = '{0}'".format(data["store"])
    )
    items = cursor.fetchall()
    if len(items) == 0:
        msg = json.dumps(
            {"type": LIST_ITEMS, "store_exist": 0, "items": items[0]}
        ).encode("UTF-8")
    else:
        msg = json.dumps(
            {"type": LIST_ITEMS, "store_exist": 1, "items": items[0]}
        ).encode("UTF-8")
    send_msg(user_s, msg)


def handle_list_store(user_s, db, data):
    cursor = db.execute("SELECT store, area_store from MARKET_TABLE")
    list_store = cursor.fetchall()
    msg = json.dumps({"type": LIST_STORE, "store": list_store}).encode("UTF-8")
    send_msg(user_s, msg)


def send_msg(user_s, msg):
    length = f"{len(msg):<{LENGTH}}".encode("UTF-8")
    print(length + msg)
    user_s.send(length + msg)


def server_down():
    sv_socket.close()
    os._exit(0)


def handle_disconnect(user_s, db, data):
    user_s.close()
    print("user disconnected")


def signal_handler(signal, frame):
    server_down()


def accept_user():
    while True:
        user_s, user_add = sv_socket.accept()
        print("Accepted socket ")
        send_th = threading.Thread(target=handle_data, args=[user_s])
        send_th.start()


sv_socket = socket.socket()
# server
def sv():
    global sv_socket
    sv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sv_socket.bind((HOST, PORT))
    sv_socket.listen(10)
    print("server starting...")
    accept_user()


sv()
