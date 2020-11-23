import socket
import sys
import colorama 

from math import ceil
from threading import Thread
from datetime import datetime, timedelta
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
        global serverTimezone
        global clientTimezone
        
        userName = input("Enter your username: ")
        
        clientTimezone = strftime("%z", gmtime())
        
        serverTimezone = clientSocket.recv(BLOCK_SIZE).decode("utf-8")
        print(type(clientTimezone))
        
         
        
    def _send():
        while True:
            
            msg = f"{userName}\2{input()}\1".encode("utf-8")
            
            try:
                clientSocket.send(msg)
                
            except ConnectionResetError:
                handleException()
                
           
           
    def _receive():
        
        msg = ""
        
        while True:
            try:
                data = clientSocket.recv(BLOCK_SIZE).decode("utf-8")     
                               
                if not data:
                    break
                    
                if ("\1" in data):
                    data = data.split("\1")
                    if (not msg):
                        _print_msg(data[0])
                    else:
                        msg += data[0]
                        _print_msg(msg)
                        msg = ""
                else:
                    msg += data
                
                
            except ConnectionResetError:
                handleException()
            
                
            
            
    def _fix_time(serverTz, clientTz, now):
        now = datetime.fromtimestamp(float(now))
          
        return now
        
        
    def _print_msg(msg):
        if ("\2" in msg):
            data = msg.split("\2")
            
            if (clientTimezone != serverTimezone):
                data[0] = _fix_time(serverTimezone, clientTimezone, data[0])
            else:
                data[0] = datetime.fromtimestamp(float(data[0]))
            
            
            print(f'{GREEN}<{data[0]}> [{data[1]}]: {RESET}{data[2]}')
        else:
            print(msg)
        
       
       
             
    def handleException():
        print("The server shutted down the connection")
        
        sys.exit(1)
        clientSocket.close()
        
    
    
    print(CLEAR_SCREEN)


    _init_socket()
     
    

    
if __name__ == '__main__':
    main()
    