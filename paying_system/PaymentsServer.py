import logging
import random
import socket
import string
import threading

import psycopg2

from FirstTask.CustomSocket import CustomSocket

HOST = '127.0.0.1'
PORT = 8090
HEADER_LENGTH = 10
USERS_EXPECTED_NUMBER = 20

server_socket = CustomSocket()
connections = {}  # [addr][connection]

users_online = {}  # [addr][num of wallet]

sql_get_wallet_num_by_name = "SELECT user_wallet_num FROM users WHERE user_wallet_num=%s" \
                             " AND user_password=crypt(%s, user_password);"
sql_insert_new_user_data = "INSERT INTO users (user_name, user_password, user_wallet_num, user_sum) VALUES " \
                           "(%s, crypt(%s, gen_salt('f')), %s, 100) ON CONFLICT DO NOTHING RETURNING 'OK';"
sql_get_all_other_wallets = "SELECT user_name, user_wallet_num FROM users WHERE NOT user_wallet_num=%s;"
sql_subtract_sum = "UPDATE users SET user_sum = user_sum - %s WHERE user_wallet_num = %s RETURNING 'OK';"
sql_add_sum = "UPDATE users SET user_sum = user_sum + %s WHERE user_wallet_num = %s RETURNING 'OK';"
sql_get_sum = "SELECT user_sum FROM users WHERE user_wallet_num=%s;"


def get_cursor_connection():
    connection = psycopg2.connect(dbname='infrastructure_3d_db', user='postgres', password='supersecurepassword',
                                  host='127.0.0.1')
    return connection.cursor(), connection


def connect_users():
    for user in range(USERS_EXPECTED_NUMBER):
        conn, addr = server_socket.accept()

        if conn not in connections:
            connections[addr] = conn
            threading.Thread(target=process_message, args=(addr,)).start()
        print(f'Connection with user at address {addr} has been established')
        threading.Thread(target=connect_users).start()


def build_msg(msg_type, msg_text, params=None):
    if msg_type in [2, 4, 5] and params:
        msg_text = b'\0'.join([bytes(d, 'utf-8') for d in [msg_text, params[0]]])  # text \0 wallet number
    elif msg_type == 3:
        msg_text = bytes(msg_text, 'utf-8')
        for user_data in params[0]:
            msg_text += b'\0'.join([bytes(d, 'utf-8') for d in user_data])
    else:
        msg_text = bytes(msg_text, 'utf-8')
    text_len = len(msg_text)
    msg = bytearray([msg_type])
    msg += bytes(f'{text_len:<{HEADER_LENGTH - 1}}', 'utf-8') + msg_text
    print(f'Reply for command {msg_type} has been created')


def process_message(user):
    while True:
        try:
            message_type, data_header, data = receive_data(user)
            # close the user connection if smth is wrong with the data received
            # different actions on different message type
            if message_type == 1:  # sign in
                print(f'User with address {user} wants to sign in')
                signed_in = sign_in(user, data[0], data[1])
                sign_in_response = 'You have been successfully logged in' if signed_in else 'Wrong user credentials'
                connections[user].send(build_msg(message_type, sign_in_response))
            elif message_type == 2:
                print(f'User with address {user} wants to sign up')
                registered_wallet_num = register(user, data[0], data[1])
                register_response = 'You have been successfully registered' if registered_wallet_num else \
                    'User with this name already exists'
                connections[user].send(build_msg(message_type, register_response, (registered_wallet_num,)))
            elif message_type == 3:
                print(f'User {users_online[user]} wants to see info about other users')
                existing_wallets = get_existing_wallets(user)
                connections[user].send(build_msg(message_type, 'Existing users:', (existing_wallets,)))
            elif message_type == 4:
                print(f'User {users_online[user]} wants to send {data[1]}€ to user {data[0]}')
                user_new_sum = transfer_sum(users_online[user], data[0],
                                            data[1])  # from what wallet, to what wallet, sum to transfer
                msg = build_msg(message_type, 'Transaction was successful. Your balance...',
                                (str(user_new_sum),)) if user_new_sum else build_msg(message_type,
                                                                                     'Error occurred! Check your'
                                                                                     ' balance and receiver wallet'
                                                                                     ' number.')
                connections[user].send(msg)
            elif message_type == 5:
                print(f'User {users_online[user]} want to know how much money he has on the account')
                sum_on_account = get_sum_on_account(users_online[user])
                connections[user].send(build_msg(message_type, 'Your balance:', (str(sum_on_account), )))
            elif message_type == 6:  # user wants to quit. send goodbye
                print(f'User {users_online[user]} wants to leave the server')
                connections[user].send(build_msg(message_type, 'Leaving server...'))
                close_user_connection(user)
            else:
                pass
        except ConnectionResetError as ex:
            print(f'User {users_online[user]} has disconnected unexpectedly:')
            logging.error(ex)
            close_user_connection(user)
            return False


def sign_in(user, name, password):
    cursor, connection = get_cursor_connection()
    cursor.execute(sql_get_wallet_num_by_name, (name, password))
    wallet_num = cursor.fetchall()[0][0]
    connection.commit()

    if not wallet_num:
        return False
    else:
        users_online[user] = wallet_num
        return True


def register(user, name, password):
    cursor, connection = get_cursor_connection()
    wallet_num = ''.join(random.choices(string.digits, k=16))
    cursor.execute(sql_insert_new_user_data, (name, password, wallet_num))
    was_successful = cursor.fetchall()[0][0]
    connection.commit()

    if was_successful:
        users_online[user] = wallet_num
    return wallet_num if was_successful else None


def get_existing_wallets(user):
    cursor, connection = get_cursor_connection()
    cursor.execute(sql_get_all_other_wallets, (users_online[user],))
    wallets = cursor.fetchall()
    connection.commit()
    return wallets


def transfer_sum(sender_wallet_num, receiver_wallet_num, sum_to_transfer):
    user_new_sum = None
    cursor, connection = get_cursor_connection()
    cursor.execute(sql_subtract_sum, (sum_to_transfer, sender_wallet_num))
    sum_subtracted = cursor.fetchall()[0][0]
    if sum_subtracted:
        cursor.execute(sql_add_sum, (sum_to_transfer, receiver_wallet_num))
        sum_added = cursor.fetchall()[0][0]
        if sum_added:
            cursor.execute(sql_get_sum, (sender_wallet_num,))
            user_new_sum = cursor.fetchall()[0][0]
    connection.commit()
    return user_new_sum


def get_sum_on_account(wallet_num):
    cursor, connection = get_cursor_connection()
    cursor.execute(sql_get_sum, (wallet_num,))
    sum_on_account = cursor.fetchall()[0][0]
    connection.commit()
    return sum_on_account


def receive_data(user):
    data_header = server_socket.receive_bytes_num(HEADER_LENGTH, connections[user])
    if not data_header:
        return False, False
    message_type = data_header[0]
    data_length = int(data_header[1:].decode().strip())
    data = None
    if data_length:
        data = server_socket.receive_bytes_num(data_length, connections[user])
        data = [d.decode() for d in data.split(b'\0')]
    return message_type, data_header, data


def close_user_connection(user):
    connections[user].shutdown(socket.SHUT_WR)
    connections[user].close()
    print(f'Client {users_online[user]} has been disconnected')
    del connections[user]
    del users_online[user]


def run_server():
    server_socket.setsockopt()
    server_socket.bind(HOST, PORT)
    server_socket.listen(USERS_EXPECTED_NUMBER)
    print('Waiting for clients to connect...')

    while True:
        pass


def main(host_name, port):
    global HOST
    global PORT
    HOST = host_name
    PORT = port

    threading.Thread(target=run_server()).start()
