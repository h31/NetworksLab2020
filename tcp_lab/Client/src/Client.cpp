#include "Client.h"

#include <stdio.h>
#include <stdlib.h>

#include <WinSock2.h>
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
#include <string.h>

#define MAXDATASIZE 256 // max number of bytes we can get at once 

// get sockaddr, IPv4:
void* get_in_addr(struct sockaddr* sa)
{
    return &(((struct sockaddr_in*)sa)->sin_addr);
}

namespace Tcp_lab {

    Client::~Client()
    {
        closesocket(m_SocketFd);
        //Cleanup winsock
        WSACleanup();
    }

    bool Client::Initialize(PCSTR NodeName, PCSTR ServiceName)
    {
        InitializeWinSock2();

        memset(&m_Hints, 0, sizeof m_Hints);
        m_Hints.ai_family   = AF_INET;
        m_Hints.ai_socktype = SOCK_STREAM;

        int rv = getaddrinfo(NodeName, ServiceName, &m_Hints, &m_ServInfo);
        if (rv != 0)
        {
            fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(rv));
            return false;
        }

        if (m_ServInfo == NULL)
        {
            fprintf(stderr, "ERROR connection failed\n");
            return false;
        }

        m_SocketFd = socket(m_ServInfo->ai_family, m_ServInfo->ai_socktype, m_ServInfo->ai_protocol);
        if (m_SocketFd == -1)
        {
            perror("ERROR opening socket");
            return false;
        }

        if (connect(m_SocketFd, m_ServInfo->ai_addr, m_ServInfo->ai_addrlen) == -1)
        {
            closesocket(m_SocketFd);
            perror("ERROR connection failed");
            return false;
        }

        inet_ntop(m_ServInfo->ai_family, get_in_addr((struct sockaddr*)m_ServInfo->ai_addr),
            s, sizeof s);
        printf("client: connecting to %s\n", s);

        freeaddrinfo(m_ServInfo); // all done with this structure
        return true;
    }

    void Client::SetNickname(char* nickname)
    {
        m_Name = std::string(nickname);
    }

    void Client::RecieverRun()
    {
        int numbytes = 0;
        char buffer[MaxMessageSize];
        char Name[NameMaxSize];
        char Message[MessageMaxSize];
        MessageInfo Info;

        while (m_IsRunning)
        {
            bzero(buffer, MaxMessageSize);
            bzero(Name, NameMaxSize);
            bzero(Message, MessageMaxSize);

            numbytes = recv(m_SocketFd, buffer, MessageMaxSize, 0);
            // Reading server response
            if (numbytes == -1)
            {
                perror("ERROR reading from socket");
                m_IsRunning = false;
                return;
            }
            else
            {
                Desearilize(buffer, &Info, Name, Message);
                time_t time = static_cast<time_t>(Info.m_Time);
                struct tm* tmp = gmtime(&time);

                printf("<%i:%i> [%s] %s\n", tmp->tm_hour, tmp->tm_min, Name, Message); 
            }
        }
    }

    void Client::SenderRun()
    {
        char MessageBuf[MessageMaxSize];
        char buff[MaxMessageSize];
        size_t TotalSize = 0;

        while (m_IsRunning)
        {
            bzero(MessageBuf, MessageMaxSize);
            bzero(buff, MaxMessageSize);
            TotalSize = 0;

            if (fgets(MessageBuf, MessageMaxSize, stdin) != NULL)
            {
                Serialize(buff, m_Name.c_str(), MessageBuf, m_Name.length(), strlen(MessageBuf));
                TotalSize = m_Name.length() + strlen(MessageBuf) + sizeof(MessageInfo);
            }

            // Sending message to the server
            if (send(m_SocketFd, buff, TotalSize, 0) < 0 && m_IsRunning)
            {
                perror("ERROR writing to socket");
                m_IsRunning = false;
                return;
            }
        }
    }
}
int main(int argc, char* argv[])
{
    if (argc < 3)
    {
        fprintf(stderr, "usage: %s hostname port nickname(not necessarily)\n", argv[0]);
        return 1;
    }

    Tcp_lab::Client Client;
    if (argc == 4)
    {
        Client.SetNickname(argv[3]);
    }
    bool isInitialized = Client.Initialize(argv[1], argv[2]);
    if (isInitialized)
    {
        Client.Reciever = std::thread(&Tcp_lab::Client::RecieverRun, &Client);
        Client.Sender = std::thread(&Tcp_lab::Client::SenderRun, &Client);
        Client.Reciever.join();
    }
    return 0;
}
