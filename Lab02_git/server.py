import socket
import itertools, sys
import selectors

from threading import Thread
from datetime import datetime, timedelta
from time import gmtime, strftime, sleep



HOST = '127.0.0.1'
PORT = 8080
BLOCK_SIZE = 1024

connectedUsers = []
tzCoefficients = []

selector = selectors.DefaultSelector()


def main():

    #serverTz = strftime("%z", gmtime())
    
    def _init():  
        global serverSocket
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind((HOST, PORT))
        serverSocket.listen(5)
        serverSocket.setblocking(False)
        sys.stdout.write('\b')
        print('waiting for connection...')
        selector.register(serverSocket, selectors.EVENT_READ, _connect)     
        
        
        
    def _connect(mask):
        global conn
        timezoneData = strftime("%z", gmtime()).encode("utf-8")
        conn, address = serverSocket.accept()
        conn.setblocking(False)
        sys.stdout.write('\b')
        print ('connected:', address)
        connectedUsers.append(conn)
        conn.send(timezoneData)
        selector.register(conn, selectors.EVENT_READ, _send)
           
         
            
    def _send(conn):
        try:
            data = conn.recv(BLOCK_SIZE)
            
            if not data:
                print('closing', conn)
                sel.unregister(conn)
                conn.close() 
            
            messageEndFlag = ("\1").encode("utf-8")
            messageHeaderFlag = ("\2").encode("utf-8")
                 
            for receiver in connectedUsers:
                now = datetime.now()
                currentTime = datetime.timestamp(now)   
                try:
                    if ((messageHeaderFlag) in data):
                        timeToAppend = f"{currentTime}\2".encode("utf-8")
                        fixedData = timeToAppend + data
                        receiver.send(fixedData)
                    else:
                        receiver.send(data)
                except ConnectionResetError:
                    pass 
                        
        except ConnectionResetError:
            pass                 
      
    
    _init()
    
   
    while True:
            events = selector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj)
        
        
if __name__ == '__main__':
    main()

        
    
