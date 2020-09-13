#pragma once

#include "Server.h"

#include <stdio.h>
#include <stdlib.h>
#include <utility>
#include <string.h>

#include <assert.h>

namespace Tcp_lab {

    Server::Server()
    {
        InitializeWinSock2();

        m_Sockfd = socket(AF_INET, SOCK_STREAM, 0);
        if (m_Sockfd < 0)
        {
            perror("ERROR opening socket");
            assert(0);
        }

        /* Initialize socket structure */
        bzero((char*)&m_ServerAddr, sizeof(m_ServerAddr));
        m_PortNum = 5001;

        m_ServerAddr.sin_family = AF_INET;
        m_ServerAddr.sin_addr.s_addr = INADDR_ANY;
        m_ServerAddr.sin_port = htons(m_PortNum);

        /* Now bind the host address using bind() call.*/
        if (bind(m_Sockfd, (struct sockaddr*)&m_ServerAddr, sizeof(m_ServerAddr)) < 0)
        {
            perror("ERROR on binding");
            exit(1);
        }
    }

    Server::~Server()
    {
        //close socket
        closesocket(m_Sockfd);
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
        listen(m_Sockfd, 5); 
        clilen = sizeof(cli_addr);

        while (true)
        {
            /* tracking of incoming connection */
            newsockfd = accept(m_Sockfd, (struct sockaddr*)&cli_addr, &clilen);

            if (newsockfd < 0)
            {
                printf("Error on accept: %i", WSAGetLastError());
                exit(1);
            }
            else
            {
                std::lock_guard<std::mutex> guard(m_Mutex);
                m_SocketToThreadMap[newsockfd] = std::thread(&Tcp_lab::Server::ClientRun, this, newsockfd, cli_addr, clilen);
            }
        }
    }

    void Server::CleanThread(SOCKET ClientSocket)
    {
        std::lock_guard<std::mutex> guard(m_Mutex);
        std::thread& thread = m_SocketToThreadMap[ClientSocket];
        while (thread.joinable()) {}
        m_SocketToThreadMap.erase(ClientSocket);
    }

    void Server::ClientRun(SOCKET ClientSocket, struct sockaddr_in ClientAddr, int ClientLen)
    {
        char buffer[MaxMessageSize]; //buffer for command
        int bytesnum; //result code

        while (true)
        {
            bzero(buffer, MaxMessageSize);

            /* Wait for message from client */
            bytesnum = recv(ClientSocket, buffer, MaxMessageSize, 0); // recv on Windows
            if (bytesnum < 0)
            {
                perror("Client Disconnected");
                shutdown(ClientSocket, SD_BOTH);
                return;
            }

            printf("recived %i bytes\n", bytesnum);

            std::lock_guard<std::mutex> guard(m_Mutex);
            /*Broadcasting the sended message*/
            for (auto SocketToThread = m_SocketToThreadMap.begin(); SocketToThread != m_SocketToThreadMap.end(); ++SocketToThread)
            {
                SOCKET broadcastingSocket = SocketToThread->first;
                if (broadcastingSocket != INVALID_SOCKET && broadcastingSocket != ClientSocket)
                {
                    send(broadcastingSocket, buffer, bytesnum, 0);
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
