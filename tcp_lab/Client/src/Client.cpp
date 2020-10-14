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

        u_long mode = 1;  // 1 to enable non-blocking socket
        //ioctlsocket(SocketFd, FIONBIO, &mode);

        return true;
    }

    void Client::Deinitialize()
    {
        shutdown(SocketFd, SD_BOTH);
    }

    void Client::SetNickname(LPCWCH nickname, unsigned long readedBytes)
    {
       bzero(Name, NameMaxSize * sizeof(wchar_t));
       size_t requiredBytesNum = WideCharToMultiByte(CP_UTF8, 0, nickname, readedBytes, Name, NameMaxSize, NULL, NULL);
       Name[requiredBytesNum] = '\0';
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

            numbytes = recv(SocketFd, buffer, 1024, 0);
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
#ifdef CLIENT_DEBUG
                std::printf("MAXBUFFERSIZE :  %i\n", MaxBufferSize);
                std::printf("Number of recieved bytes :  %i\n", numbytes);
#endif
                Desearilize(buffer, &Info, Name, Message);
                time_t time = static_cast<time_t>(Info.Time);
                struct tm* exactTime = std::localtime(&time);
                
                std::printf("<%i:%i> [%s] : %s\n", exactTime->tm_hour, exactTime->tm_min, Name, Message);
            }
        }
    }

    void Client::SenderRun()
    {
        char buff[MaxBufferSize]; //final output buffer
        CHAR MessageBuf[MessageMaxSize];
        //PTCHAR wstr = new TCHAR[WideMessageMaxSize]; //buffer in wide char
        TCHAR wstr[WideMessageMaxSize];
        size_t TotalSize = 0;

        while (IsRunning)
        {
            //clear all buffers and counters
            bzero(MessageBuf, MessageMaxSize); 
            bzero(buff, MaxBufferSize); 
            bzero(wstr, MessageMaxSize);
            TotalSize = 0;
            unsigned long readedBytes = 0; //size of readed bytes

            if (ReadConsole(StdinHandle, wstr, WideMessageMaxSize, &readedBytes, NULL))
            {
                size_t requiredBytesNum = WideCharToMultiByte(CP_UTF8, 0, wstr, readedBytes, MessageBuf, sizeof(MessageBuf), NULL, NULL);

                if (strlen(MessageBuf) > MessageMaxSize)
                {
                    Serialize(buff, Name, MessageBuf, strlen(Name), MessageMaxSize);
                    TotalSize = sizeof(uint16_t) + strlen(Name) + MessageMaxSize + sizeof(MessageInfo);
                }
                else
                {
                    Serialize(buff, Name, MessageBuf, strlen(Name), strlen(MessageBuf) - 1);
                    TotalSize = sizeof(uint16_t) + strlen(Name) + strlen(MessageBuf) + sizeof(MessageInfo);
                }
            }

            if (TotalSize > sizeof(MessageInfo))
            {
#ifdef CLIENT_DEBUG
                printf("DEBUG strlen size message: %i\n", strlen(MessageBuf));
                printf("TOTAL SIZE: %i\n", TotalSize);
#endif
                // Sending message to the server
                if (send(SocketFd, buff, TotalSize, 0) < 0 && IsRunning)
                {
                    //perror("ERROR writing to socket");
                    if (WSAGetLastError() == WSAENOTSOCK)
                    {
                        printf("Socket operation on nonsocket: %i\n", SocketFd);
                    }
                        
                   
                    //IsRunning = false;
                    //return;
                }
            }
        }
    }

    void Client::PrintDebug()
    {
        printf("Name Length %i\n", strlen(Name));
        printf("Struct size %i\n", sizeof(MessageInfo));
        printf("DEBUG MAX message: %i\n", MessageMaxSize);
    }
}

inline bool IsEven(size_t First, size_t Second)
{
    return (First / Second) & 1;
}

int main(int argc, char* argv[])
{
    Tcp_lab::Client Client;
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);
    
    {
        TCHAR WideCharPtr[MessageMaxSize]; //buffer in wide char
        unsigned long readedBytes = 0; //size of readed bytes
        ReadConsole(Client.StdinHandle, WideCharPtr, NameMaxSize, &readedBytes, NULL);
        //WideCharPtr[readedBytes / sizeof(wchar_t) + 1] = L'\0';
        Client.SetNickname(WideCharPtr, readedBytes - 2);
    }

    bool isInitialized = false;
    if (argc < 3)
    {
#ifdef CLIENT_DEBUG
        Client.PrintDebug();
#endif
        //fprintf(stderr, "usage: %s hostname port if want to not local addr\n", argv[0]);
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
        Client.Deinitialize();
    }
    return 1;
}
