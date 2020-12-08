import os
import paying_system.PaymentsServer as PS
import threading


def main():
    while True:
        pass


if __name__ == '__main__':
    os.system('PaymentsServer.py 127.0.0.1 8090')
    #threading.Thread(target=PS.main('127.0.0.1', 8090)).start()
    print('blah')
    main()

