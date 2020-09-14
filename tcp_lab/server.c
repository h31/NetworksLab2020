#include <sys/socket.h>
#include <stdio.h>
#include <string.h>
#include <arpa/inet.h>
#include <pthread.h>

#define MAXDATASIZE 256

//Global variables
pthread_mutex_t threadChat;
int clients[20];
int n=0;

void sendToClient(char *msg,int tmp){
	int i;
	pthread_mutex_lock(&threadChat);
	for(i = 0; i < n; i++) {
		if(clients[i] != tmp) {
			if(send(clients[i],msg,strlen(msg),0) < 0) {
				printf("sending failure n");
				continue;
			}
		}
	}
	pthread_mutex_unlock(&threadChat);
}

void *recvmg(void *client_sock){
	int sock = *((int *)client_sock);
	char msg[MAXDATASIZE];
	int len;
	while((len = recv(sock, msg, MAXDATASIZE, 0)) > 0) {
		msg[len] = '\0';
		sendToClient(msg, sock);
	}
	
}

int main(int argc, char *argv[]){
	struct sockaddr_in serverIP;
	pthread_t recvt;
	int sockfd = 0, clientSock=0;
	uint16_t portno;
	
	portno = atoi(argv[1]);

	serverIP.sin_family = AF_INET;
	serverIP.sin_port = htons(portno);
	serverIP.sin_addr.s_addr = inet_addr("127.0.0.1");
	sockfd = socket(AF_INET, SOCK_STREAM, 0);
	
	if( bind( sockfd, (struct sockaddr *)&serverIP, sizeof(serverIP)) == -1 )
		printf("cannot bind, error!!\n");
	else
		printf("Server Started\n");
		
	if( listen(sockfd, 20) == -1 )
		printf("listening failed\n");
		
	while(1){
		if( (clientSock = accept(sockfd, (struct sockaddr *)NULL,NULL)) < 0 )
			printf("accept failed  n");
		pthread_mutex_lock(&threadChat);
		clients[n]= clientSock;
		n++;
		// creating a thread for each client 
		pthread_create(&recvt,NULL,(void *)recvmg, &clientSock);
		pthread_mutex_unlock(&threadChat);
	}
	return 0; 
	
}
