import socket
import json
import sys
import os

HEADER_LENGTH = 4

SIGN_IN = "00"
SIGN_UP = "01"
MAKE_ORDER = "02"
CONFIRM_BUY = "03"
HISTORY_BUYER = "04"
HISTORY_SELLER = "05"
ADD_STORE = "06"
VIEW_LIST_ITEMS = "07"
VIEW_LIST_STORES = "08"
SIGN_OUT = "09"


ip = sys.argv[1]
port = int(sys.argv[2])
username = ""


cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def main():
    try:
        print("FOOD DELIVERY APPLICATION")
        while True:
            to_do = input(
                """
                What would you like to do?
                1) sign in for seller
                2) sign up for seller
                3) sign in for buyer
                4) sign up for buyer
                """
            )

            if to_do == "1":
                # seller sign in
                print("sign in for seller")
                sign_in_up("seller", SIGN_IN)
            elif to_do == "2":
                # seller sign up
                print("sign up for seller")
                sign_in_up("seller", SIGN_UP)
            elif to_do == "3":
                # buyer sign in
                print("sign in for buyer")
                sign_in_up("buyer", SIGN_IN)
            elif to_do == "4":
                # buyer sign up
                print("sign up for buyer")
                sign_in_up("buyer", SIGN_UP)
            else:
                print("Input invalid")
                continue

            if to_do == "1" or to_do == "2":
                print("Using seller interface")
                seller_interface()
            else:
                print("Using buyer interface")
                buyer_interface()
    except:
        print("Disconnected")


def sign_in_up(role, type_msg):
    global username
    ck = False
    while not ck:
        id = input("Input id: ")
        password = input("Input your password: ")
        msg_json = {"type": type_msg, "user": id, "password": password, "role": role}
        send_msg(msg_json)
        msg_accepted = recv_msg()
        print(msg_accepted["msg"])
        ck = msg_accepted["accepted"]
        if ck == False:
            print("Enter id and password again: ")
        else:
            print("SUCCESS")
            username = msg_json["user"]


def buyer_interface():
    while True:
        to_do = input(
            """
        What would you like to do?
        1) Create an order
        2) Get history about your orders
        3) Get list store
        4) Get information about store (products in store)
        5) Disconnect from server
        """
        )

        if to_do == "1":
            print("Enter name of shop, your zone and list of product")
            msg_order()
        elif to_do == "2":
            msg_history(HISTORY_BUYER)
        elif to_do == "3":
            msg_get_list_store()
        elif to_do == "4":
            msg_get_inform_store()
        elif to_do == "5":
            sign_out()
        else:
            print("Input invalid")


def msg_order():
    shop_name = input("Enter name of shop: ")
    zone = input("Enter your zone: ")
    items = input("Enter list of product (product1, product2, product3, ...): ")
    msg_json = {"type": MAKE_ORDER, "store": shop_name, "items": items, "area": zone}
    send_msg(msg_json)
    msg_confirm = recv_msg()
    print(msg_confirm)
    if msg_confirm["have_store"] == 1:
        accept_buy = input("Accept to buy? (y/n)")
        accept = False
        if accept_buy == "y":
            accept = True
        else:
            accept = False
        msg_confirm["type"] = CONFIRM_BUY
        msg_confirm["accepted"] = accept
        msg_confirm["buyer"] = username
        msg_confirm["store"] = shop_name
        send_msg(msg_confirm)
        rep_msg = recv_msg()
        print(rep_msg["msg"])


def seller_interface():
    while True:
        to_do = input(
            """
        What would you like to do?
        1) Create a store
        2) Get history of your sales
        3) Get list store
        4) Disconnect from server
        """
        )

        if to_do == "1":
            print("Enter name of shop, your zone and list of product")
            msg_add_store()
        elif to_do == "2":
            # store = input("Enter name of your store: ")
            msg_history(HISTORY_SELLER)
        elif to_do == "3":
            msg_get_list_store()
        elif to_do == "4":
            sign_out()
        else:
            print("Input invalid")


def msg_add_store():
    shop_name = input("Enter name of your shop: ")
    zone = input("Enter zone of store: ")
    items = input(
        "Enter list of product (product1:price1, product2:price2, product3:price3, ...): "
    )
    msg_json = {
        "type": ADD_STORE,
        "store": shop_name,
        "items": items,
        "area_store": zone,
        "seller": username,
    }
    send_msg(msg_json)
    msg_confirm = recv_msg()
    print(msg_confirm["msg"])


def msg_get_inform_store():
    msg_json = {
        "type": VIEW_LIST_ITEMS
    }
    shop_name = input("Enter name of your shop: ")
    msg_json["store"] = shop_name
    send_msg(msg_json)
    msg_recv = recv_msg()
    print(msg_recv)
    if msg_recv["store_exist"] == 0:
        print(f"Store {shop_name} doesn't exist")
    else:
        print(f"Products at store {shop_name}:")
        for i in range(len(msg_recv["items"])):  
            print(f"{msg_recv['items'][i]}")
            if i <= len(msg_recv["items"]) - 1:
                print(", ")


def msg_get_list_store():
    msg_json = {
        "type": VIEW_LIST_STORES
    }
    send_msg(msg_json)
    msg_recv = recv_msg()
    
    print("Store name\tzone")
    for r in msg_recv["store"]:
        print(f'{r[0]}\t{r[1]}')


def msg_history(type_history):
    msg_json = {"type": type_history}
    if type_history == HISTORY_BUYER:
        msg_json["buyer"] = username
    elif type_history == HISTORY_SELLER:
        msg_json["seller"] = username
    send_msg(msg_json)
    inform = recv_msg()
    print(inform["msg"])

def sign_out():
    msg_json = {
        "type": SIGN_OUT
    }
    print("You will disconnect from server")
    send_msg(msg_json)
    os._exit()

def recv_msg():

    msg_header = cli_sock.recv(HEADER_LENGTH).decode("utf-8").strip()
    if not len(msg_header):
        return False

    msg = json.loads(cli_sock.recv(int(msg_header)).decode("utf-8"))

    return msg


def send_msg(msg_json):
    msg_code = json.dumps(msg_json).encode("utf-8")
    msg_header = f"{len(msg_code):<{HEADER_LENGTH}}".encode("utf-8")
    #print(msg_code)
    cli_sock.send(msg_header + msg_code)


if __name__ == "__main__":
    cli_sock.connect((ip, port))
    main()