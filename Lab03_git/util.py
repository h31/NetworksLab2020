import colorama

colorama.init()

CLEAR_SCREEN = '\033[2J'
GREEN = '\033[32m'
YEL = '\033[33m'
RED = '\033[31m'
RESET = '\033[0m'

serviceMode = True


def makeBytes(data):
    return data.to_bytes(2, "big")


def checkIfFileExists(data):
    filename = str(data).split('\\x')[2][2:]
    try:
        f = open(f'f/{filename}')
        f.close()
        return True
    except FileNotFoundError:
        return False


def writeFileBytes(filename, data):
    with open(filename, 'wb') as f:
        f.write(data)


def printServiceMessage(msg):
    if (serviceMode):
        print(f'SERVICE MESSAGE: ' + msg)


def printMenu():
    print(f"{GREEN}You are using TFTP client. Aviable commands:{RESET}\n"
          f"{YEL}send <filename>{RESET}{GREEN} - send file to the default server directory{RESET}\n"
          f"{YEL}get  <filename>{RESET}{GREEN} - get file from the default server directory{RESET}\n"
          f"{YEL}help           {RESET}{GREEN} - print this menu{RESET}")


def printError(msg):
    print(f"{RED}{msg}{RESET}")


def printMessage(msg):
    print(f'{GREEN}{msg}{RESET}')
