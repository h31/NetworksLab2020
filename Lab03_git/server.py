import socket
from util import printServiceMessage as serviceMsg, checkIfFileExists as checkFile, writeFileBytes
from packageGenerator import generatePackage, ERROR, OPCODE
from random import randint
from transmissionHandler import getterHandler

HOST = "127.0.0.1"
PORT = 69
BLOCK_SIZE = 512
TIMEOUT = 2000


def writeFile(data, address):
    writeSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    writeSocket.bind((HOST, randint(1024, 65535)))
    writeSocket.settimeout(TIMEOUT)

    filename = str(data).split('\\x')[2][2:]

    if checkFile(data):
        serviceMsg(f'File already exists.')
        ERRpackage = generatePackage(type=OPCODE['ERROR'], errorCode=6)
        writeSocket.sendto(ERRpackage, address)
        serviceMsg(f'Sent error to client: {address}. Raw data: {ERRpackage}')
        return
    else:

        ACKpackage = generatePackage(type=OPCODE['ACK'], blockNumber=0)
        writeSocket.sendto(ACKpackage, address)
        serviceMsg(f'Sent ACK after WRQ to client: {address}. Raw data: {ACKpackage}. Block number: {0}')

        fileData = getterHandler(writeSocket, BLOCK_SIZE)

        if (fileData is not None):
            writeFileBytes(f'f/{filename}', fileData)
            serviceMsg(f'Successfully wrote data to f/{filename}')
            writeSocket.close()
            return
        else:
            return


def sendFile(data, address):
    blocksToSend = []
    sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sendSocket.bind((HOST, randint(1024, 65535)))
    sendSocket.settimeout(TIMEOUT)

    filename = str(data).split('\\x')[2][2:]
    try:
        with open(f'f/{filename}', 'rb') as f:
            for byte in iter(lambda: f.read(BLOCK_SIZE), b''):
                blocksToSend.append(byte)

    except FileNotFoundError:
        serviceMsg(f'File doesn\'t exist.')
        ERRpackage = generatePackage(type=OPCODE['ERROR'], errorCode=1)
        sendSocket.sendto(ERRpackage, address)
        serviceMsg(f'Sent error to client: {address}. Raw data: {ERRpackage}')
        return

    currentBlock = 1
    receivedACKblockNum = 1
    numberOfBlocks = len(blocksToSend)
    serviceMsg(f"Number of blocks to send: {numberOfBlocks}")

    DATApackage = generatePackage(type=OPCODE['DATA'], blockNumber=currentBlock,
                                  fileData=blocksToSend[currentBlock - 1])
    sendSocket.sendto(DATApackage, address)

    while True:
        try:
            # expecting ACK after DATA
            data, server = sendSocket.recvfrom(BLOCK_SIZE + 4)
        except socket.timeout:
            serviceMsg(f'Did not receive ACK after DATA. Resending DATA.')
            DATApackage = generatePackage(type=OPCODE['DATA'], blockNumber=receivedACKblockNum + 1,
                                          fileData=blocksToSend[receivedACKblockNum + 1])
            sendSocket.sendto(DATApackage, server)
            serviceMsg(f'Re-sent block #{currentBlock}')
            continue
        except ConnectionResetError:
            serviceMsg(f'Lost connection')
            return

        if (data[1] == OPCODE['ACK']):

            # https://coderwall.com/p/x6xtxq/convert-bytes-to-int-or-int-to-bytes-in-python
            receivedACKblockNum = 256 * data[2] + data[3]
            serviceMsg(f'Received ACK from client. Raw data: {data}. Block number: {receivedACKblockNum}')

            # sending data
            try:
                DATApackage = generatePackage(type=OPCODE['DATA'], blockNumber=receivedACKblockNum + 1,
                                              fileData=blocksToSend[receivedACKblockNum])
            except:
                serviceMsg(f'All blocks sent.')
                sendSocket.close()
                return
            sendSocket.sendto(DATApackage, server)
            serviceMsg(f'Sent block #{receivedACKblockNum + 1}')

            currentBlock = currentBlock + 1

        elif (data[1] == OPCODE['ERROR']):
            serviceMsg(f'Received ERROR from client: {ERROR[data[3]]}')
            return


def main():
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverSocket.bind((HOST, PORT))
    print(f"Listening on port {PORT}...")

    while True:
        data, address = serverSocket.recvfrom(BLOCK_SIZE)

        if (data[1] == OPCODE['RRQ']):
            serviceMsg(f'Received RRQ from {address}. Raw data: {data}')
            sendFile(data, address)
        elif (data[1] == OPCODE['WRQ']):
            serviceMsg(f'Received WRQ from {address}. Raw data: {data}')
            writeFile(data, address)


if __name__ == '__main__':
    main()
