
#include <stdio.h>
#include <stdlib.h>
#include <chrono>
#include <ctime>
#include <memory.h> //memcpy
#include <string>
#include <thread>
#include <tchar.h>


//Windows socket headers
#include <stdint.h> //fixed size types
#include <WinSock2.h>
#include <ws2ipdef.h>

#define bzero(buffer, len) (memset((buffer), '\0', (len)), (void) 0)  

#include <WS2tcpip.h>
#include <AF_Irda.h>
#include <in6addr.h>
#include <mstcpip.h>
#include <MSWSock.h>
#include <nsemail.h>
#include <NspAPI.h>
#include <socketapi.h>
//#include <SpOrder.h>
#include <transportsettingcommon.h>
#include <winsock.h>
#include <WS2atm.h>
#include <WS2spi.h>
#include <wsipv6ok.h>
#include <WSNwLink.h>
#include <wsrm.h>

void InitializeWinSock2()
{
    //Initialize Winsock
    WSADATA WsaData;
    WORD DLLVersion = MAKEWORD(2, 2);
    //if Initializing is ok
    if (WSAStartup(DLLVersion, &WsaData) != 0)
    {
        std::printf("WinSock process initialized with error\n");
        exit(1);
    }
}

