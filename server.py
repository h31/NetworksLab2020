import socket
import itertools, sys

from threading import Thread
from datetime import datetime, timedelta
from time import gmtime, strftime, sleep



HOST = '127.0.0.1'
PORT = 8080
BLOCK_SIZE = 1024

connectedUsers = []
tzCoefficients = []


def main():

    serverTz = strftime("%z", gmtime())
    
    def _init():  
    
        global serverSocket
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind((HOST, PORT))
        serverSocket.listen(5)
        sys.stdout.write('\b')
        print('waiting for connection...')
        Thread(target = _connect).start()
        
        
        
    def _connect():
        global conn
        timezoneData = strftime("%z", gmtime()).encode("utf-8")
        
        while True:
            conn, address = serverSocket.accept()
            sys.stdout.write('\b')
            print ('connected:', address)
            connectedUsers.append(conn)
            conn.send(timezoneData)
            
            Thread(target = _send, args = (conn,)).start()
            
            
    
    def _send(conn):
        try:
        
            while True:
                data = conn.recv(BLOCK_SIZE).decode("utf-8")
                
                if not data:
                    break
                   
                
                for receiver in connectedUsers:
                    now = datetime.now()
          
                    currentTime = datetime.timestamp(now)
                    
                    try:
                        if (len(data.split("\2")) > 1):
                            receiver.send((f"{currentTime}\2{data}").encode("utf-8"))
                        else:
                            receiver.send(data.encode("utf-8"))
                            
                    except ConnectionResetError:
                        pass
                    
        except ConnectionResetError:
            pass
                 
                 
    
    def _spinner():
        spinner = itertools.cycle(['-', '/', '|', '\\'])
        while True:
            sys.stdout.write(next(spinner))   
            sys.stdout.flush()               
            sys.stdout.write('\b')
            sleep(0.2)
        
        
    Thread(target = _init).start()
    Thread(target = _spinner).start()
    
   
        
if __name__ == '__main__':
    main()

        
    
