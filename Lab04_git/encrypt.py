import hashlib


def encrypt_password(string):
    hexadecimal = hashlib.md5(string.encode())
    return hexadecimal.hexdigest()
