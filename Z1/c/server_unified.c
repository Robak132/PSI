#include <stdio.h>
#include <string.h>
#include <sys/socket.h>

#include <stdlib.h>
#include <arpa/inet.h>

#include <netinet/in.h>
#include <sys/select.h>

#include <unistd.h>

#define BUFFER 1024  //Max length of buffer
#define PORT_V6 8886   //The port on which to listen for incoming data for IPv6
#define PORT_V4 8884   //The port on which to listen for incoming data for IPv4

int main(void)
{
    // IPv4 variables
    struct sockaddr_in server_addr_v4, client_addr_v4;
    int sock_v4_fd, slen = sizeof(client_addr_v4), recv_len;
    
    // IPv4 initial config and stuff
    //create a UDP socket
    if ((sock_v4_fd=socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1) {
        perror("socket");
        exit(1);
    }

    // zero out the structure
    memset((char *) &server_addr_v4, 0, sizeof(server_addr_v4));

    server_addr_v4.sin_family = AF_INET;
    server_addr_v4.sin_port = htons(PORT_V4);
    server_addr_v4.sin_addr.s_addr = inet_addr("127.0.0.1");

    // bind socket to port
    if(bind(sock_v4_fd, (struct sockaddr*)&server_addr_v4, sizeof(server_addr_v4)) < 0) {
        perror("bind");
        exit(1);
    }

    printf("Successfully bound IPv4 server.\n");

    // IPv6 variables
    fd_set socket_fds; // socket file descriptors
    struct sockaddr_in6 server_addr_v6, client_addr_v6;
    socklen_t client_length;
    int sock_v6_fd;
    int bytes_received;
    char buf[BUFFER];

    sock_v6_fd = socket(PF_INET6, SOCK_DGRAM, 0);
    if (sock_v6_fd < 0)
    {
        perror("Unable to create socket.");
        return -1;
    }

    memset( &server_addr_v6, 0, sizeof( server_addr_v6 ) );
    server_addr_v6.sin6_family = AF_INET6;
    server_addr_v6.sin6_addr = in6addr_any;
    server_addr_v6.sin6_port = htons( PORT_V6 );

    if (bind( sock_v6_fd, (struct sockaddr *)&server_addr_v6, sizeof( server_addr_v6 )) < 0)
    {
        perror("Unable to bind.");
        return -1;
    }
    printf("Successfully bound IPv6 server.\n");

    printf("sock_v4_fd: %d\n", sock_v4_fd);
    printf("sock_v6_fd: %d\n", sock_v6_fd);

    while (1)
    {
        FD_ZERO(&socket_fds);
        FD_SET(sock_v6_fd, &socket_fds);
        FD_SET(sock_v4_fd, &socket_fds);

        int fd_max = sock_v6_fd > sock_v4_fd ? sock_v6_fd : sock_v4_fd;

        int retval = select(fd_max + 1, &socket_fds, NULL, NULL, NULL);
        printf("retval: %d\n", retval);
        if (retval == -1)
        {
            printf("Select error\n");
            return -1;
        }
        else if (retval == 0)
        {
            printf("timeout. Wut???\n");
        }
        else
        {
            if (FD_ISSET(sock_v4_fd, &socket_fds))
            {
                // try to receive some data, this is a blocking call
                if ((recv_len = recvfrom(sock_v4_fd, buf, BUFFER, 0, (struct sockaddr *) &client_addr_v4, &slen)) < 0) {
                    perror("Error in recvfrom.");
                    break;
                }
                //print details of the client/peer and the data received
                printf("Received packet from %s:%d\n", inet_ntoa(client_addr_v4.sin_addr), ntohs(client_addr_v4.sin_port));
                printf("Data: %s\n" , buf);
            }
            else if (FD_ISSET(sock_v6_fd, &socket_fds))
            {
                int client_length = sizeof(client_addr_v6);
            
                if ((bytes_received = recvfrom(sock_v6_fd, buf, BUFFER, 0, (struct sockaddr *) &client_addr_v6, &client_length)) < 0)
                {
                    perror("Error in recvfrom.");
                    break;
                }
                
                char client_addr_v6_char[INET6_ADDRSTRLEN];
                inet_ntop(AF_INET6, &client_addr_v6.sin6_addr, client_addr_v6_char, INET6_ADDRSTRLEN);

                //print details of the client/peer and the data received
                printf("Received packet from %s:%d\n", client_addr_v6_char, ntohs(client_addr_v6.sin6_port));
                printf("Data: %s\n\n" , buf);
            }
            else 
            {
                printf("Brak nowych wiadomosci. Wut???\n");
            }
        }

    }

    return 0;
}
