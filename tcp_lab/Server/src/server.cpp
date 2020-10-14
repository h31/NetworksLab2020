#include "Server.h"

#include <utility>
#include <assert.h>

namespace Tcp_lab {

#define DEFAULT_CLIENT_COUNT 100

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

        ClientsPollInfo.reserve(DEFAULT_CLIENT_COUNT);
        ClientsPollInfo.push_back(WSAPOLLFD{ Sockfd, POLLIN | POLLOUT, 0 });

        u_long mode = 1;  // 1 to enable non-blocking socket
        ioctlsocket(Sockfd, FIONBIO, &mode);
    }

    Server::~Server()
    {
        //close all connections
        for (auto PollInfo = ClientsPollInfo.begin(); PollInfo != ClientsPollInfo.end(); ++PollInfo)
        {
            SOCKET broadcastingSocket = PollInfo->fd;
            shutdown(broadcastingSocket, SD_RECEIVE);
            closesocket(broadcastingSocket);
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
        char buffer[MaxBufferSize];
        int32_t index = 1;

        //Transform state of socket to listening
        int answer = listen(Sockfd, 5); 
        
        if (answer < 0)
        {
            printf("Error on setting to Listening %i \n", WSAGetLastError());
            closesocket(Sockfd);
            return;
        }

        while (IsRunning)
        {
            /* tracking of incoming connection */
            int32_t ClientCount = WSAPoll(&ClientsPollInfo[0], ClientsPollInfo.size(), 1);

            if (ClientCount == SOCKET_ERROR) //== -1
            {
                //Error
                std::printf("Error on poll: %i \n", WSAGetLastError());
            }
            else if (ClientCount == 0)
            {
                //timeout
            }
            else
            {
                //printf("DEBUG %i \n", ClientCount);

                //To validate data between users, firstly need to accept new connections
                //because incoming messages need to be sended to this users too
                if (ClientsPollInfo[0].revents & POLLIN)
                    AcceptIncomingConnections();

                index = 1;

                //processing all in polling
                for (size_t i = 0; i < ClientCount; i++)
                {
                    //Get index of socket when processing is stopped
                    //if return -1 there is nothing to be processing
                    int32_t recieving = BroadcastMessages(buffer, index);
                    if (recieving < 0)
                    {
                        std::printf("Error on recieving: %i \n", WSAGetLastError());
                    }
                    else
                    {
                        index = recieving;
                    }
                }
            }
        }
    }

    const bool Server::AcceptIncomingConnections()
    {
        SOCKET newsockfd;
        int clilen;
        struct sockaddr_in cli_addr;
        clilen = sizeof(cli_addr);

        do
        {
            newsockfd = accept(Sockfd, (struct sockaddr*)&cli_addr, &clilen);

            //printf("NEWSOCK %i \n", newsockfd);

            /*if (newsockfd == -1)
            {
                std::printf("Error on accept: %i \n", WSAGetLastError());
                return false; //No one want to connect
            }
            else*/
            if (newsockfd != -1)
            {
                ClientsPollInfo.push_back( {newsockfd, POLLIN | POLLOUT, 0} );
                std::printf("Client connected: adress [%i] port [%i], New clients count: %i\n", cli_addr.sin_addr, cli_addr.sin_port, ClientsPollInfo.size());
            }
        } while (newsockfd != -1);
        return true;
    }

    const int32_t Server::BroadcastMessages(char* buffer, const int32_t index)
    {
        for (size_t i = index; i < ClientsPollInfo.size(); i++)
        {
            WSAPOLLFD& ClientSockPollFd = ClientsPollInfo[i];
            if (ClientSockPollFd.revents & POLLIN)
            {
                bzero(buffer, MaxBufferSize);
                //read without blocking
                const int numbytes = recv(ClientSockPollFd.fd, buffer, MessageMaxSize, 0);
                //ClientSockPollFd.revents ^= POLLIN; //sub POLLIN flag

                if (numbytes <= 0)
                {
                    printf("deleting user \n");
                    ClientsPollInfo.erase(ClientsPollInfo.begin() + index);
                    shutdown(ClientSockPollFd.fd, SD_RECEIVE);
                    return -1;
                }

                 //Broadcasting
                for (auto it = ClientsPollInfo.begin() + 1; it != ClientsPollInfo.end(); it++)
                {
                    //POLLOUT - ready to send to send data 
                    //to this socket without blocking
                    //broadcast send without blocking
                    const bool ReadyToGetDataOnSocket = it->revents & POLLOUT;
                    const bool SocketIsNotInvalidAndSame = it->fd != INVALID_SOCKET && it->fd != ClientSockPollFd.fd;
                    if (SocketIsNotInvalidAndSame && ReadyToGetDataOnSocket)
                    {
                        send(it->fd, buffer, numbytes, 0);
                        //it->revents ^= POLLOUT;
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
    return 1;
}
