#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <sys/socket.h>

#define BUFFER 1024  //Max length of buffer
#define PORT 8888   //The port on which to listen for incoming data

int main(void)
{
    struct sockaddr_in si_me, si_other;

    int s, slen = sizeof(si_other), recv_len;
    char buf[BUFFER];

    //create a UDP socket
    if ((s=socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1) {
        perror("socket");
        exit(1);
    }

    // zero out the structure
    memset((char *) &si_me, 0, sizeof(si_me));

    si_me.sin_family = AF_INET;
    si_me.sin_port = htons(PORT);
    si_me.sin_addr.s_addr = inet_addr("127.0.0.1");

    // bind socket to port
    if(bind(s, (struct sockaddr*)&si_me, sizeof(si_me)) == -1) {
        perror("bind");
        exit(1);
    }

    // keep listening for data
    while(1) {
        printf("Waiting for data... ");
        fflush(stdout);

        // try to receive some data, this is a blocking call
        if ((recv_len = recvfrom(s, buf, BUFFER, 0, (struct sockaddr *) &si_other, &slen)) == -1) {
            perror("recvfrom()");
            exit(1);
        }

        //print details of the client/peer and the data received
        printf("Received packet from %s:%d\n", inet_ntoa(si_other.sin_addr), ntohs(si_other.sin_port));
        printf("Data: %s\n" , buf);
    }

    return 0;
}
