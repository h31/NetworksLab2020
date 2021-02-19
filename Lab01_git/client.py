import socket
import sys
import colorama 

from threading import Thread
from datetime import datetime
from time import gmtime, strftime

colorama.init()


HOST = '127.0.0.1'
PORT = 8080
BLOCK_SIZE = 1024


CLEAR_SCREEN = '\033[2J'
GREEN = '\033[32m' 
RESET = '\033[0m'



def main():

    def _init_socket():
        global clientSocket
        
        try: 
            clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientSocket.connect((HOST, PORT))  
            
            _init_user()
                    
            Thread(target = _receive).start()
            Thread(target = _send).start()
            
        except ConnectionRefusedError:
            print ("The server is unreachable")
        
        
        
    def _init_user():
        global userName
        
        userName = input("Enter your username: ")
        
        timezoneData = f'\2{strftime("%z", gmtime())}'.encode("utf-8")
        
        try:
            clientSocket.send(timezoneData)
                
        except ConnectionResetError:
                handleException()
        
         
        
    def _send():
        while True:
            
            msg = f"\1[{userName}]:\1 {input()}\1".encode("utf-8")
            
            try:
                clientSocket.send(msg)
                
            except ConnectionResetError:
                handleException()
                
           
           
    def _receive():
        
        longMessage = ""
        
        while True:
            try:
                data = clientSocket.recv(BLOCK_SIZE).decode("utf-8")
                
                if not data:
                    break
   
                msg = data.split("\1") 
                
                    
                if (len(msg) == 5):
                
                    header = msg[1] + msg[2]
                    text = msg[3] 
                    
                    print (GREEN + header + RESET + text)
                    
                    longMessage = ""
                    
                elif (len(msg) == 4):
                    header = msg[1] + msg[2]
                    longMessage = longMessage + msg[3]
                elif (len(msg) == 1):
                    longMessage = longMessage + data
                else:
                    print (GREEN + header + RESET + longMessage + data.rstrip("\1"))
                             
                
            except ConnectionResetError:
                handleException()
                
       
             
    def handleException():
        print("The server shutted down the connection")
        sys.exit(1)
        
    
    
    print(CLEAR_SCREEN)


    _init_socket()
     
    

    
if __name__ == '__main__':
    main()
    