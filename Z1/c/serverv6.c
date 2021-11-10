#include <stdio.h>
#include <string.h>
#include <sys/socket.h>

#include <stdlib.h>
#include <arpa/inet.h>

#include <netinet/in.h>
#include <sys/select.h>

#define BUFFER 1024  //Max length of buffer
#define PORT_V6 8886   //The port on which to listen for incoming data

int main(void)
{
    fd_set socket_fds; // socket file descriptors
    struct sockaddr_in6 server_addr, client_addr;
    socklen_t client_length;
    int sock_v6_fd, sock_v4_fd;
    int bytes_received;
    char buffer[BUFFER];

    FD_ZERO(&socket_fds);
    FD_SET(sock_v6_fd, &socket_fds);


    sock_v6_fd = socket(PF_INET6, SOCK_DGRAM, 0);
    if (sock_v6_fd < 0)
    {
        perror("Unable to create socket.");
        return -1;
    }

    memset( &server_addr, 0, sizeof( server_addr ) );
    server_addr.sin6_family = AF_INET6;
    server_addr.sin6_addr = in6addr_any;
    server_addr.sin6_port = htons( PORT_V6 );

    if (bind( sock_v6_fd, (struct sockaddr *)&server_addr, sizeof( server_addr )) < 0)
    {
        perror("Unable to bind.");
        return -1;
    }
    printf("Successfully bound IPv6 server.\n");
    printf("sock_v6_fd: %d\n", sock_v6_fd);

    while (1)
    {
        FD_ZERO(&socket_fds);
        FD_SET(sock_v6_fd, &socket_fds);


        int retval = select(sock_v6_fd + 1, &socket_fds, NULL, NULL, NULL);
        printf("retval: %d\n", retval);
        if (retval == -1)
        {
            printf("Select error\n");
            //error
        }
        else if (retval == 0)
        {
            printf("timeout. Wut???\n");
        }
        else
        {
            if (FD_ISSET(sock_v6_fd, &socket_fds))
            {
                int client_length = sizeof(client_addr);
            }
            
            if ((bytes_received = recvfrom(sock_v6_fd, buffer, BUFFER, 0, (struct sockaddr *) &client_addr, &client_length)) < 0)
                {
                    perror("Error in recvfrom.");
                    break;
                }


                char client_addr_v6[INET6_ADDRSTRLEN];
                inet_ntop(AF_INET6, &client_addr.sin6_addr, client_addr_v6, INET6_ADDRSTRLEN);
                //print details of the client/peer and the data received
                printf("Received packet from %s:%d\n", client_addr_v6, ntohs(client_addr.sin6_port));
                printf("Data: %s\n\n" , buffer);
        }
    }

    return 0;
}
