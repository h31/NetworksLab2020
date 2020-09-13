#pragma once

#include "Server.h"

#include <stdio.h>
#include <stdlib.h>

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
                perror("ERROR on accept");
                exit(1);
            }
            else
            {
                m_ClientSockets.emplace_back(newsockfd);
                m_ChatThreads.emplace_back(std::thread(&Tcp_lab::Server::ClientRun, this, m_ChatThreads.size(), cli_addr, clilen));
            }
        }
    }

    void Server::ClientRun(size_t IndexInSocketArray, struct sockaddr_in ClientAddr, int ClientLen)
    {
        SOCKET ClientSocket = m_ClientSockets[IndexInSocketArray]; //client Socket
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

            /*Broadcasting the sended message*/
            for (size_t i = 0; i < m_ClientSockets.size(); i++)
            {
                if (m_ClientSockets[i] != INVALID_SOCKET && i != IndexInSocketArray)
                {
                    send(m_ClientSockets[i], buffer, bytesnum, 0);
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
