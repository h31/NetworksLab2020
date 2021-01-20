import socket
import threading
import os
import sqlite3
import json
import hashlib

HOST = "0.0.0.0"
PORT = 5000
HEADER_LENGTH = 8

SIGN_IN = "0"
SIGN_UP = "1"
WRITE_MAIL = "2"
VIEW_SENT_BOX = "3"
VIEW_RECEIVED_BOX = "4"
READ_MAIL = "5"
VIEW_LIST_USER = "6"
DISCONNECT_FROM_SERVER = "7"

connected_list = {}
online_user = {}


sv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sv_sock.bind((HOST, PORT))


def main():
    print("Sever listening")
    sv_sock.listen(10)
    while True:
        cli_sock, cli_addr = sv_sock.accept()
        print("Accepted connect")
        connected_list[cli_addr] = cli_sock
        handler_thread = threading.Thread(target=handle_request, args=(cli_addr,))
        handler_thread.start()


def handle_request(cli_addr):
    db = sqlite3.connect(database="mail-db.db")
    while True:
        try:
            rq = recv_msg(cli_addr)
        except:
            print("user disconnected")
            break
        print(rq)
        if not rq:
            pass
        else:
            print(rq)
            type_msg = rq["type"]
            print(type_msg)
            if type_msg == SIGN_UP:
                print("go to sign up")
                handle_sign_up(cli_addr, db, rq)
            elif type_msg == SIGN_IN:
                handle_sign_in(cli_addr, db, rq)
            elif type_msg == WRITE_MAIL:
                handle_write_mail(cli_addr, db, rq)
            elif type_msg == VIEW_SENT_BOX:
                handle_view_sent_box(cli_addr, db, rq)
            elif type_msg == VIEW_RECEIVED_BOX:
                handle_view_received_box(cli_addr, db, rq)
            elif type_msg == READ_MAIL:
                handle_read_mail(cli_addr, db, rq)
            elif type_msg == VIEW_LIST_USER:
                handle_view_list_user(cli_addr, db)
            elif type_msg == DISCONNECT_FROM_SERVER:
                print(
                    f"user on {cli_addr} with user_name {rq['id']} need to be disconnected from server"
                )
                close_connection(cli_addr, rq["id"])


def handle_sign_up(cli_addr, db, rq):
    cursor = db.execute(
        "SELECT user_name, user_password from USERS WHERE user_name = '{0}';".format(
            rq["id"]
        )
    )
    rows = cursor.fetchall()
    msg = {"type": SIGN_UP, "success": False, "msg": ""}
    if len(rows) == 1:
        msg["msg"] = "User already exist"
    else:
        password_hash = hashlib.sha256(str(rq["password"]).encode("utf-8"))
        db.execute(
            "INSERT INTO USERS (user_name, user_password) VALUES ('{0}', '{1}') ;".format(
                rq["id"], password_hash
            )
        )
        db.commit()
        msg["success"] = True
        msg["msg"] = "Sign up succeeded"
        online_user[rq["id"]] = connected_list[cli_addr]

    send_msg(msg, cli_addr)


def handle_sign_in(cli_addr, db, rq):
    password_hash = hashlib.sha256(str(rq["password"]).encode("utf-8"))
    cursor = db.execute(
        "SELECT user_name, user_password from USERS WHERE user_name = '{0}' and user_password = '{1}';".format(
            rq["id"], password_hash
        )
    )
    rows = cursor.fetchall()
    msg = {"type": SIGN_IN, "success": False, "msg": ""}
    if len(rows) == 0:
        msg["msg"] = "User or Password invalid"
    else:
        msg["success"] = True
        msg["msg"] = "Login success"
        online_user[rq["id"]] = connected_list[cli_addr]

    send_msg(msg, cli_addr)


def handle_write_mail(cli_addr, db, rq):
    cursor = db.execute(
        "SELECT * from USERS where user_name = '{0}'".format(rq["receive_id"])
    )
    rows = cursor.fetchall()
    msg = {
        "type": WRITE_MAIL,
    }
    if len(rows) == 0:
        msg["exist_id"] = False
        msg["msg"] = "Receiver does not exist"
    else:
        db.execute(
            "INSERT INTO MAIL_BOX (sender_id, receiver_id, header_mail, content, unread) VALUES ('{0}', '{1}', '{2}', '{3}', {4})".format(
                rq["send_id"], rq["receive_id"], rq["header_mail"], rq["mail"], True
            )
        )
        db.commit()
        msg["exist_id"] = True
        msg["msg"] = "Successful mailing"

    send_msg(msg, cli_addr)


def handle_view_sent_box(cli_addr, db, rq):
    cursor = db.execute(
        "SELECT sender_id, receiver_id, header_mail from MAIL_BOX where sender_id = '{0}'".format(
            rq["id"]
        )
    )
    rows = cursor.fetchall()
    msg = {"type": VIEW_SENT_BOX, "inform": rows}
    if len(rows) == 0:
        msg["msg"] = "You have no mail in sent box"
    else:
        msg["msg"] = f"You have {len(rows)} mail(s) in sent box\n"

    send_msg(msg, cli_addr)


def handle_view_received_box(cli_addr, db, rq):
    cursor = db.execute(
        "SELECT sender_id, receiver_id, header_mail, unread from MAIL_BOX where receiver_id = '{0}'".format(
            rq["id"]
        )
    )
    rows = cursor.fetchall()
    msg = {"type": VIEW_RECEIVED_BOX, "inform": rows}
    if len(rows) == 0:
        msg["msg"] = "You have no mail in received box"
    else:
        msg["msg"] = f"You have {len(rows)} mail(s) in received box"
    send_msg(msg, cli_addr)


def handle_read_mail(cli_addr, db, rq):
    cursor = db.execute(
        "SELECT * from MAIL_BOX WHERE header_mail = '{0}' and (sender_id = '{1}' or receiver_id = '{2}')".format(
            rq["header_mail"], rq["id"], rq["id"]
        )
    )
    rows = cursor.fetchall()
    msg = {"type": READ_MAIL, "inform": []}
    if len(rows) == 0:
        msg["exist_mail"] = False
        msg["msg"] = "This mail does not exist"
    else:
        msg["exist_mail"] = True
        for r in rows:
            msg["inform"].append((r[0], r[1], r[2], r[3]))
        db.execute(
            "UPDATE MAIL_BOX SET unread = False WHERE header_mail = '{0}' and receiver_id = '{1}'".format(
                rq["header_mail"], rq["id"]
            )
        )
        db.commit()

    send_msg(msg, cli_addr)


def handle_view_list_user(cli_addr, db):
    cursor = db.execute("SELECT user_name from USERS")
    rows = cursor.fetchall()
    msg = {"type": VIEW_LIST_USER, "list_user": ""}
    if len(rows) == 0:
        msg["list_user"] = "No user yet"
    else:
        for r in rows:
            msg["list_user"] += f"{r[0]}\n"
    send_msg(msg, cli_addr)


def close_connection(cli_addr, id):
    connected_list[cli_addr].shutdown(socket.SHUT_WR)
    connected_list[cli_addr].close()
    print(f"user on {cli_addr} has disconnected")
    if id in online_user.keys():
        del online_user[id]
    del connected_list[cli_addr]


def recv_msg(cli_addr):
    cli_sock = connected_list[cli_addr]
    msg_header = cli_sock.recv(HEADER_LENGTH)
    # if not len(msg_header):
    #     # return False
    msg = json.loads(cli_sock.recv(int(msg_header)).decode("utf-8"))
    return msg


def send_msg(msg_json, cli_addr):
    msg_code = json.dumps(msg_json).encode("utf-8")
    msg_header = f"{len(msg_code):<{HEADER_LENGTH}}".encode("utf-8")
    print(msg_code)
    connected_list[cli_addr].send(msg_header + msg_code)


if __name__ == "__main__":
    main()