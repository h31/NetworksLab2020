#include <netdb.h>
#include <netinet/in.h>
#include <unistd.h>

#define send(socket, buffer, length, flag) write(socket, buffer, length) 
#define recv(socket, buffer, length, flag) read(socket, buffer, length);
#define WSACleanup()
#define InitializeWinSock2() 