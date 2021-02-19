import socket
from util import printServiceMessage as serviceMsg, printError
from packageGenerator import generatePackage, ERROR, OPCODE


def getterHandler(getterSocket, BLOCK_SIZE):
    currentBlock = 0
    receivedBefore = 0
    fileData = b''

    while True:
        currentBlock = currentBlock + 1
        try:
            data, address = getterSocket.recvfrom(BLOCK_SIZE + 4)  # expecting DATA

        except socket.timeout:
            serviceMsg(f'Did not receive data')
            continue

        if (data[1] == OPCODE['DATA']):
            # https://coderwall.com/p/x6xtxq/convert-bytes-to-int-or-int-to-bytes-in-python
            receivedBlockNumber = 256 * data[2] + data[3]
            serviceMsg(
                f'Received DATA from {address}. Received block number: {receivedBlockNumber}. Block len: {len(data)}')

            ACKpackage = generatePackage(type=OPCODE['ACK'], blockNumber=receivedBlockNumber)
            getterSocket.sendto(ACKpackage, address)

            serviceMsg(
                f'Sent ACK after DATA to server: {address}. Raw data: {ACKpackage}. Block number: {currentBlock}')

            if (receivedBlockNumber != receivedBefore):
                fileData += data[4:]

                if (len(data) < BLOCK_SIZE):
                    return fileData

            receivedBefore = receivedBlockNumber

        elif (data[1] == OPCODE['ERROR']):
            printError(f'Error on the server: {ERROR[data[3]]}')
            return None
