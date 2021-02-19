import socket
from packageGenerator import generatePackage, OPCODE, ERROR
from util import printServiceMessage as serviceMsg, printMenu, printError, printMessage, writeFileBytes
from transmissionHandler import getterHandler

HOST = "127.0.0.1"
PORT = 69
BLOCK_SIZE = 512
TIMEOUT = 5

commands = ["send", "get", "help"]


def init():
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clientSocket.settimeout(TIMEOUT)
    return clientSocket


def doSend(filename, clientSocket):
    blocksToSend = []

    try:
        with open(filename, 'rb') as f:
            for byte in iter(lambda: f.read(BLOCK_SIZE), b''):
                blocksToSend.append(byte)

    except FileNotFoundError:
        printError("Error: this file does't exist. Try again.")
        return

    WRQpackage = generatePackage(type=OPCODE['WRQ'], filename=filename)

    clientSocket.sendto(WRQpackage, (HOST, PORT))
    serviceMsg(f'Sent WRQ to server. Raw data: {WRQpackage}')

    currentBlock = 0
    numberOfBlocks = len(blocksToSend)
    serviceMsg(f"Number of blocks to send: {numberOfBlocks}")

    while True:
        try:
            # expecting ACK after DATA
            data, server = clientSocket.recvfrom(BLOCK_SIZE + 4)
        except socket.timeout:
            if (currentBlock == 0):
                serviceMsg(f'Did not receive ACK after WRQ.')
                printError("Unexpected error: try to re-send file")
                return
            else:
                serviceMsg(f'Did not receive ACK after DATA. Resending DATA.')
                DATApackage = generatePackage(type=OPCODE['DATA'], blockNumber=receivedACKblockNum + 1,
                                              fileData=blocksToSend[receivedACKblockNum + 1])
                clientSocket.sendto(DATApackage, server)
                serviceMsg(f'Re-sent block #{currentBlock}')
                continue
        except ConnectionResetError:
            printError(f'Error: server is unreachable. Try again later or restart the server.')
            return

        if (data[1] == OPCODE['ACK']):

            # https://coderwall.com/p/x6xtxq/convert-bytes-to-int-or-int-to-bytes-in-python
            receivedACKblockNum = 256 * data[2] + data[3]
            serviceMsg(f'Received ACK from server. Raw data: {data}. Block number: {receivedACKblockNum}')

            # sending data
            try:
                DATApackage = generatePackage(type=OPCODE['DATA'], blockNumber=receivedACKblockNum + 1,
                                              fileData=blocksToSend[receivedACKblockNum])
            except:
                serviceMsg(f'All blocks sent.')
                printMessage("File is sent successfully.")
                return
            clientSocket.sendto(DATApackage, server)
            serviceMsg(f'Sent block #{receivedACKblockNum + 1}')

            currentBlock = currentBlock + 1

        elif (data[1] == OPCODE['ERROR']):
            serviceMsg(f'Received ERROR from server. Raw data: {data}')
            printError(f'Error on the server: {ERROR[data[3]]}')
            return


def doGet(filename, clientSocket):
    RRQpackage = generatePackage(type=OPCODE['RRQ'], filename=filename)
    clientSocket.sendto(RRQpackage, (HOST, PORT))

    fileData = getterHandler(clientSocket, BLOCK_SIZE)

    if (fileData is not None):
        writeFileBytes(filename, fileData)
        serviceMsg(f'Successfully wrote data to {filename}')
        printMessage(f"File {filename} is successfully received.")
        return
    else:
        return


def handleCommand(command, clientSocket):
    try:
        command = command.split()
        operation = command[0]

        if (operation == "help"):
            printMenu()
        elif (len(command) != 2):
            printError(f"Wrong input: try again")
        elif (operation not in commands):
            printError(f"Wrong option: try again")
        else:
            filename = command[1]
            if (operation == "send"):
                doSend(filename, clientSocket)
            elif (operation == "get"):
                doGet(filename, clientSocket)
    except:
        raise


def run(clientSocket):
    printMenu()

    while True:  # main loop
        command = input()

        if not command:
            break

        handleCommand(command, clientSocket)


def main():
    run(init())


if __name__ == '__main__':
    main()
