#include "Client.h"

// get sockaddr, IPv4:
void* get_in_addr(struct sockaddr* sa)
{
    return &(((struct sockaddr_in*)sa)->sin_addr);
}

namespace Tcp_lab {

    Client::~Client()
    {
        closesocket(SocketFd);
        //Cleanup winsock
        WSACleanup();
    }

    bool Client::Initialize(PCSTR NodeName, PCSTR ServiceName)
    {
        struct addrinfo Hints, *ServInfo;
        char ServInfoBuffer[INET_ADDRSTRLEN];

        InitializeWinSock2();

        memset(&Hints, 0, sizeof Hints);
        Hints.ai_family   = AF_INET;
        Hints.ai_socktype = SOCK_STREAM;

        int rv = getaddrinfo(NodeName, ServiceName, &Hints, &ServInfo);
        if (rv != 0)
        {
            fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(rv));
            return false;
        }
        if (ServInfo == NULL)
        {
            fprintf(stderr, "ERROR connection failed\n");
            return false;
        }

        SocketFd = socket(ServInfo->ai_family, ServInfo->ai_socktype, ServInfo->ai_protocol);
        if (SocketFd == -1)
        {
            perror("ERROR opening socket");
            return false;
        }

        if (connect(SocketFd, ServInfo->ai_addr, ServInfo->ai_addrlen) == -1)
        {
            closesocket(SocketFd);
            perror("ERROR connection failed");
            return false;
        }

        inet_ntop(ServInfo->ai_family, get_in_addr((struct sockaddr*)ServInfo->ai_addr),
            ServInfoBuffer, sizeof ServInfoBuffer);
        printf("client: connecting to %s\n", ServInfoBuffer);

        freeaddrinfo(ServInfo); // all done with this structure
        return true;
    }

    void Client::SetNickname(PCSTR nickname)
    {
       Name = std::string(nickname);
    }

    void Client::RecieverRun()
    {
        int numbytes = 0;

        char buffer[MaxBufferSize];
        char Name[NameMaxSize];
        char Message[MessageMaxSize];
        MessageInfo Info;

        while (IsRunning)
        {
            bzero(buffer, MaxBufferSize);
            bzero(Name, NameMaxSize);
            bzero(Message, MessageMaxSize);

            numbytes = recv(SocketFd, buffer, MessageMaxSize, 0);
            // Reading server response
            if (numbytes == 0)
            {
                perror("ERROR reading disconnect");
                IsRunning = false;
                return;
            }
            else if (numbytes == -1)
            {
                perror("ERROR reading from socket");
            }
            else
            {
                Desearilize(buffer, &Info, Name, Message);
                time_t time = static_cast<time_t>(Info.Time);
                struct tm* tmp = gmtime(&time);

                std::printf("<%i:%i> [%s] : %s\n", tmp->tm_hour, tmp->tm_min, Name, Message);
            }
        }
    }

    void Client::SenderRun()
    {
        char buff[MaxBufferSize]; //final output buffer
        CHAR MessageBuf[MessageMaxSize];
        TCHAR wstr[WideMessageMaxSize]; //buffer in wide char
        size_t TotalSize = 0;

        while (IsRunning)
        {
            //clear all buffers and counters
            bzero(MessageBuf, MessageMaxSize); 
            bzero(buff, MaxBufferSize); 
            bzero(wstr, MessageMaxSize);
            TotalSize = 0;
            unsigned long readedBytes = 0; //size of readed bytes

            if (ReadConsole(StdinHandle, wstr, MessageMaxSize, &readedBytes, NULL))
            {
                size_t requiredBytesNum = WideCharToMultiByte(CP_UTF8, 0, wstr, readedBytes, MessageBuf, sizeof(MessageBuf), NULL, NULL);
                //WideCharToMultiByte(CP_UTF8, 0, wstr, readedBytes, MessageBuf, requiredBytesNum, NULL, NULL);

                if (strlen(MessageBuf) > MessageMaxSize - 1)
                {
                    Serialize(buff, Name.c_str(), MessageBuf, Name.length(), MessageMaxSize - 2);
                    TotalSize = sizeof(uint16_t) + Name.length() + MessageMaxSize + sizeof(MessageInfo);
                }
                else
                {
                    Serialize(buff, Name.c_str(), MessageBuf, Name.length(), strlen(MessageBuf) - 1);
                    TotalSize = sizeof(uint16_t) + Name.length() + strlen(MessageBuf) + sizeof(MessageInfo);
                }
            }

            if (TotalSize > sizeof(MessageInfo))
            {
                // Sending message to the server
                if (send(SocketFd, buff, TotalSize, 0) < 0 && IsRunning)
                {
                    perror("ERROR writing to socket");
                    IsRunning = false;
                    return;
                }
            }
        }
    }
}

int main(int argc, char* argv[])
{
    Tcp_lab::Client Client;
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);
    
    //if it present in console as arg
    if (argc == 4)
    {
        Client.SetNickname(argv[3]);
    }
    else
    {
        CHAR CharPtr[WideMessageMaxSize]; //buffer in simple char
        TCHAR WideCharPtr[MessageMaxSize]; //buffer in wide char
        unsigned long readedBytes = 0; //size of readed bytes
        ReadConsole(Client.StdinHandle, WideCharPtr, NameMaxSize, &readedBytes, NULL);
        size_t requiredBytesNum = WideCharToMultiByte(CP_UTF8, 0, WideCharPtr, readedBytes - 1, CharPtr, sizeof(NameMaxSize), NULL, NULL);
        //WideCharToMultiByte(CP_UTF8, 0, WideCharPtr, readedBytes - 1, CharPtr, requiredBytesNum, NULL, NULL);
        Client.SetNickname(CharPtr);
    }

    bool isInitialized = false;
    if (argc < 3)
    {
        fprintf(stderr, "usage: %s hostname port nickname(not necessarily)\n", argv[0]);
        isInitialized = Client.Initialize("127.0.0.1", "5001");
    }
    else
    {
        isInitialized = Client.Initialize(argv[1], argv[2]);
    }
    
    if (isInitialized)
    {
        Client.Reciever = std::thread(&Tcp_lab::Client::RecieverRun, &Client);
        Client.SenderRun();
    }
    return 1;
}
