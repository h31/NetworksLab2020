#include <sys/socket.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <pthread.h>

#define MAXDATASIZE 256

//Global variables
pthread_mutex_t threadChat;
int clients[20];
int n = 0;

void sendToClient(char *msg, int tmp){
	int i;
	pthread_mutex_lock(&threadChat);
	for(i = 0; i < n; i++) {
		if(clients[i] != tmp) {
			if(send(clients[i], msg, strlen(msg), 0) < 0) {
				printf("ERROR sending to clients\n");
				continue;
			}
		}
	}
	pthread_mutex_unlock(&threadChat);
}

void *recvmg(void *client_sock){
	int sock = *((int *)client_sock);
	char msg[MAXDATASIZE];
	bzero(msg, MAXDATASIZE);
	int len;
	while((len = recv(sock, msg, MAXDATASIZE, 0)) > 0) {
		msg[len] = '\0';
		sendToClient(msg, sock);
	}
	
}

int main(int argc, char *argv[]){
	struct sockaddr_in serverIP;
	pthread_t recvt;
	char *ip = "127.0.0.1";
	int sockfd = 0, clientSock = 0;
	uint16_t portno;
	
	portno = atoi(argv[1]);
	
	sockfd = socket(AF_INET, SOCK_STREAM, 0);

	if (sockfd < 0) {
		printf("ERROR opening socket");
		exit(1);
	}

	memset(&serverIP, '0', sizeof(serverIP));
	serverIP.sin_family = AF_INET;
	serverIP.sin_port = htons(portno);
	serverIP.sin_addr.s_addr = inet_addr(ip);

	/* bind the host address using bind() call.*/
	if(bind( sockfd, (struct sockaddr *)&serverIP, sizeof(serverIP)) == -1 )
		printf("ERROR on binding\n");
	else
		printf("Server Started\n");
	
	if(listen(sockfd, 20) == -1 )
		printf("ERROR listening\n");
		
	while(1){
		struct sockaddr_in cliAddr;
		unsigned int clilen;
		clilen = sizeof(cliAddr);
		memset(&cliAddr, '0', sizeof(cliAddr));
		if((clientSock = accept(sockfd, (struct sockaddr *) &cliAddr, &clilen)) < 0 )
			printf("ERROR on accept\n");
		pthread_mutex_lock(&threadChat);
		clients[n] = clientSock;
		n++;
		// Creating a thread for each client 
		pthread_create(&recvt, NULL, (void *)recvmg, &clientSock);
		pthread_mutex_unlock(&threadChat);
	}
	return 0; 
}
