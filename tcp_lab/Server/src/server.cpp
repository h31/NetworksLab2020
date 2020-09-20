#include "Server.h"

#include <utility>
#include <assert.h>

namespace Tcp_lab {

    Server::Server()
    {
        InitializeWinSock2();

        Sockfd = socket(AF_INET, SOCK_STREAM, 0);
        if (Sockfd < 0)
        {
            perror("ERROR opening socket");
            assert(0);
        }

        /* Initialize socket structure */
        bzero((char*)&ServerAddr, sizeof(ServerAddr));
        PortNum = 5001;

        ServerAddr.sin_family = AF_INET;
        ServerAddr.sin_addr.s_addr = INADDR_ANY;
        ServerAddr.sin_port = htons(PortNum);

        /* Now bind the host address using bind() call.*/
        if (bind(Sockfd, (struct sockaddr*)&ServerAddr, sizeof(ServerAddr)) < 0)
        {
            perror("ERROR on binding");
            exit(1);
        }
    }

    Server::~Server()
    {
        //close all connections
        for (auto SocketToThread = SocketToThreadMap.begin(); SocketToThread != SocketToThreadMap.end(); ++SocketToThread)
        {
            SOCKET broadcastingSocket = SocketToThread->first;
            shutdown(broadcastingSocket, SD_BOTH);
        }
        //close socket
        closesocket(Sockfd);
        //Cleanup winsock
        WSACleanup();
    }

    void Server::Run()
    {
        /* Now start listening for the clients, here process will
         * go in sleep mode and will wait for the incoming connection
         */
        int clilen;
        SOCKET newsockfd;
        struct sockaddr_in cli_addr;

        //Transform state of socket to listening
        listen(Sockfd, 5); 
        clilen = sizeof(cli_addr);

        while (true)
        {
            /* tracking of incoming connection */
            newsockfd = accept(Sockfd, (struct sockaddr*)&cli_addr, &clilen);

            if (newsockfd < 0)
            {
                printf("Error on accept: %i", WSAGetLastError());
                exit(1);
            }
            else
            {
                //std::lock_guard<std::mutex> guard(Mutex);
                SocketToThreadMap[newsockfd] = std::thread(&Tcp_lab::Server::ClientRun, this, newsockfd, cli_addr, clilen);
            }
        }
    }

    void Server::CleanThread(SOCKET ClientSocket)
    {
        std::lock_guard<std::mutex> guard(Mutex);
        std::thread& thread = SocketToThreadMap[ClientSocket];
        while (thread.joinable()) {}
        SocketToThreadMap.erase(ClientSocket);
    }

    void Server::ClientRun(SOCKET ClientSocket, struct sockaddr_in ClientAddr, int ClientLen)
    {
        char buffer[MaxBufferSize]; //buffer for command
        int bytesnum; //result code
        uint8_t counter = 0;

        while (true)
        {
            bzero(buffer, MaxBufferSize);

            /* Wait for message from client */
            bytesnum = recv(ClientSocket, buffer, MaxBufferSize, 0); // recv on Windows
            if (bytesnum == 0)
            {
                std::lock_guard<std::mutex> guard(Mutex);
                perror("Client Disconnected");
                shutdown(ClientSocket, SD_BOTH);
                SocketToThreadMap[ClientSocket].detach();
                size_t ClientCount = SocketToThreadMap.size();
                SocketToThreadMap.erase(ClientSocket);
                printf("Clients Count updated: new %i, was %i ", SocketToThreadMap.size(), ClientCount);
                return;
            }
            else if (bytesnum == -1)
            {
                if (++counter > 5)
                {
                    perror("Client Disconnected with Error");
                    shutdown(ClientSocket, SD_BOTH);
                    return;
                }
            }
            else
            {
                printf("recived %i bytes\n", bytesnum);

                //std::lock_guard<std::mutex> guard(Mutex);
                /*Broadcasting the sended message*/
                for (auto SocketToThread = SocketToThreadMap.begin(); SocketToThread != SocketToThreadMap.end(); SocketToThread++)
                {
                    SOCKET broadcastingSocket = SocketToThread->first;
                    if (broadcastingSocket != INVALID_SOCKET && broadcastingSocket != ClientSocket)
                    {
                        send(broadcastingSocket, buffer, bytesnum, 0);
                    }
                }
            }
        }
    }
};

int main()
{
    Tcp_lab::Server Server;
    Server.Run();

    return 0;
}
