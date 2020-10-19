import socket
import sys
from threading import Thread
from datetime import datetime

HOST = 'localhost'
PORT = 8080
BLOCK_SIZE = 1024


def main():
    
    def _init():
        global clientSocket
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((HOST, PORT))      
        Thread(target = _receive).start()
        Thread(target = _send).start()
        
             
        
    def _send():
        global clientSocket
        userName = input("Enter your username: ")
        
        while True:
            msg = input()
            now = datetime.now()
            currentTime = now.strftime("%H:%M:%S")
            
            try:
                clientSocket.send(("[" + userName + "]" + "<" + currentTime + ">" + ": " + msg).encode("utf-8"))
            except ConnectionResetError:
                handleException()
                
           
           
    def _receive():
        global clientSocket
        
        while True:
            try:
                data = clientSocket.recv(BLOCK_SIZE).decode("utf-8")
                if not data:
                    break
                print(data)
            except ConnectionResetError:
                handleException()
                
             
             
    def handleException():
        print("The server shutted down the connection")
        sys.exit(1)
        

    _init()
     
    

    
if __name__ == '__main__':
    main()
    