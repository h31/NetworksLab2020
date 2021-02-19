import socket
from threading import Thread
from datetime import datetime, timedelta
from time import gmtime, strftime



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
        print('waiting for connection...')
        Thread(target = _connect).start()
        
        
        
    def _connect():
        global conn
        
        while True:
            conn, address = serverSocket.accept()
            print ('connected:', address)
            connectedUsers.append(conn) 

            _recv_tzinfo()
            
            Thread(target = _send, args = (conn,)).start()
            
            
            
    def _recv_tzinfo():
    
        try:
            timezoneData = conn.recv(BLOCK_SIZE).decode("utf-8").split("\2")[1]
            tzCoefficients.append(timezoneData)
            
        except IndexError:
            tzCoefficients.append("ERR_NO_DATA")
    
    
    
    def _send(conn):
        try:
            while True:
                data = conn.recv(BLOCK_SIZE).decode("utf-8")
                
                if not data:
                    break
                   
                
                for receiver in connectedUsers:
                    now = datetime.now()
                
                    if (tzCoefficients[connectedUsers.index(receiver)] != serverTz):
                        now = _fix_time(serverTz, tzCoefficients[connectedUsers.index(receiver)], now)
                        
                    currentTime = now.strftime("%H:%M:%S")
                        
                    
                    try:
                        if (data[0] == "\1"):
                            receiver.send((f"\1<{currentTime}>  {data}").encode("utf-8"))
                        elif (data[0] == "\2"):
                            pass
                        else:
                            receiver.send(data.encode("utf-8"))
                            
                    except ConnectionResetError:
                        print("This user disconnected")
                    
        except ConnectionResetError:
            pass
                 
    
    
    def _fix_time(serverTz, clientTz, now):
        
        if (clientTz == "ERR_NO_DATA"):
            pass
            
        else:
            coefficient = int(serverTz) / 100 - int(clientTz) / 100
            now = now - timedelta(hours = coefficient)
            
        return now
               
        
        
    Thread(target = _init).start()
    
   
        
if __name__ == '__main__':
    main()

        
    
