import socket
import os
import signal
import sqlite3
import json
import sys

HOST = sys.argv[1]
PORT = int(sys.argv[2])
LENGTH = 8
username = ""

SIGN_IN = "0"
SIGN_UP = "1"
MAIL = "2"
SENT_MAIL = "3"
RCV_MAIL = "4"
READ_MAIL = "5"
LIST_USER = "6"
DISCONNECT = "7"
cli_socket = socket.socket()

# client


def user_sign():
    print("MAIL TRANSFER")

    while True:
        action = input(
            "SIGN IN OR SIGN UP\n\t1-Sign in\n\t2-Sign up\nPress 1 to sign in or 2 to sign up: "
        )
        if action == "1":
            handle_sign(SIGN_IN)
            break
        elif action == "2":
            handle_sign(SIGN_UP)
            break
        else:
            print("Has no option for action <{0}>\n".format(action))
    ui()


def handle_sign(action):
    global username
    accept = False
    while not accept:
        username = input("Login\t: ")
        password = input("Password: ")
        msg = json.dumps({"type": action, "id": username, "password": password}).encode(
            "UTF-8"
        )
        send_to_server(msg)
        data = recv_from_server()
        try:
            if data["type"]:
                accept = data["success"]
                print(data["msg"])
        except:
            print("SOME THING WRONG")


def ui():
    while True:
        action = input("Choose your option (h for help): ")
        if action == "h":
            print(
                "USER OPTIONS:\n\t 1-Compose mail\n\t 2-View inbox\n\t 3-View send box\n\t 4-Read mail \n\t 5-All user information\n\t 6-Disconnect \n"
            )
        elif action == "1":
            handle_new_mail()
        elif action == "2":
            handle_inbox(RCV_MAIL)
        elif action == "3":
            handle_inbox(SENT_MAIL)
        elif action == "4":
            handle_read_mail()
        elif action == "5":
            handle_list_user()
        elif action == "6":
            handle_disconnect()
        else:
            print("FORMAT USER OPTION WRONG")


def handle_new_mail():
    again = True
    while again:
        dest = input("Send to\t:")
        header = input("Mail header\t:")
        content = input("Write your email after this:...\n")
        msg = json.dumps(
            {
                "type": MAIL,
                "send_id": username,
                "receive_id": dest,
                "header_mail": header,
                "mail": content,
            }
        ).encode("UTF-8")
        send_to_server(msg)
        data = recv_from_server()
        if data["type"] != MAIL:
            print("WRONG TYPE NEW MAIL RECEIVE")
            os._exit(0)
        if data["exist_id"] == True:
            print(data["msg"])
            break
        else:
            print(data["msg"])
            while True:
                write_again = input("Do you want write again ?(y/n):")
                if write_again == "y":
                    again = True
                    break
                elif write_again == "n":
                    again = False
                    break
                else:
                    print("WRONG FORMAT OPTION WRITE AGAIN")


def handle_read_mail():
    header = input("Input header mail to read:")
    msg = json.dumps({"type": READ_MAIL, "header_mail": header, "id": username}).encode(
        "UTF-8"
    )
    send_to_server(msg)
    data = recv_from_server()
    if data["type"] != READ_MAIL:
        print("WRONG TYPE NEW MAIL RECEIVE")
        os._exit(0)
    if data["exist_mail"] == False:
        print("No mail name {0}".format(header))
    else:
        for d in data["inform"]:
            print("from: " + d[0] + "-------- " + d[2] + " --------" "to: " + d[1])
            print(d[3] + "\n")


def handle_list_user():
    msg = json.dumps({"type": LIST_USER}).encode("UTF-8")
    send_to_server(msg)
    data = recv_from_server()
    if data["type"] != LIST_USER:
        print("WRONG TYPE LIST USER RECEIVE")
        os._exit(0)
    else:
        print("LIST USER:")
        print(data["list_user"])
        print("\n")


def handle_inbox(action):
    msg = json.dumps(
        {
            "type": action,
            "id": username,
        }
    ).encode("UTF-8")
    send_to_server(msg)
    data = recv_from_server()
    if data["type"] != action:
        print("WRONG TYPE INFORMATION INBOX RECEIVE")
        os._exit(0)
    print(data["msg"])
    if action == SENT_MAIL:
        for d in data["inform"]:
            print("form: {0}\t to: {1}\t ----- Header: {2}".format(d[0], d[1], d[2]))
    elif action == RCV_MAIL:
        state = ""
        for d in data["inform"]:
            if d[3] == 1:
                state = "unread"
            else:
                state = "read"
            print(
                "form: {0}\t to: {1}\t ----- {2} ----- {3}".format(
                    d[0], d[1], d[2], state
                )
            )


def handle_disconnect():
    msg = json.dumps({"type": DISCONNECT, "id": username}).encode("UTF-8")
    send_to_server(msg)
    os._exit(1)


def send_to_server(msg):
    length = f"{len(msg):<{LENGTH}}".encode("UTF-8")
    cli_socket.send(length + msg)


def recv_from_server():
    length_d = cli_socket.recv(LENGTH)
    if len(length_d) == 0:
        os._exit(1)
    else:
        data = cli_socket.recv(int(length_d.decode("UTF-8")))
        data = json.loads(data.decode("UTF-8"))
    return data


def signal_handler(signal, frame):
    os._exit(0)


def cl():
    global cli_socket
    cli_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cli_socket.connect((HOST, PORT))
    signal.signal(signal.SIGINT, signal_handler)
    user_sign()


cl()
