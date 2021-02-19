import hashlib


def encryptPassword(string):
    hexRes = hashlib.md5(string.encode())
    return hexRes.hexdigest()
