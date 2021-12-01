// Server side C/C++ program to demonstrate Socket programming
#include <unistd.h>
#include <cstdio>
#include <sys/socket.h>
#include <cstdlib>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <string>
#include <cstring>
#include <iostream>
#include <csignal>

#define ADDRESS_V4 "127.0.0.1"
#define PORT_V4 8888

#define ADDRESS_V6 "::1"
#define PORT_V6 8888

#define BUFFER_SIZE 102400

class Server {
private:
    int socket_fd, connection_socket;
    struct sockaddr_in socket_address;
    int socket_address_len = sizeof(socket_address);
    char buffer[BUFFER_SIZE] = {0};
    char str_addr[INET_ADDRSTRLEN];
    std::string protocol;
public:
    Server(std::string protocol_name="IPv4") {
        protocol = protocol_name;
        socket_fd = setup_socket();
        // Listen
        if (listen(socket_fd, 3) < 0) {
            perror("listen");
            exit(EXIT_FAILURE);
        }
        std::cout << protocol << ": Opened socket connection" << std::endl;
    }
    int setup_socket() {
        // Create socket file descriptor
        if ((socket_fd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) == 0) {
            perror("socket failed");
            exit(EXIT_FAILURE);
        }

        // Setup socket
        memset((char *) &socket_address, 0, sizeof(socket_address));
        socket_address.sin_family = AF_INET;
        socket_address.sin_addr.s_addr = inet_addr(ADDRESS_V4);
        socket_address.sin_port = htons(PORT_V4);

        int opt = 1;
        if (setsockopt(socket_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt))) {
            perror("setsockopt");
            exit(EXIT_FAILURE);
        }

        // Bind socket to address
        if (bind(socket_fd, (struct sockaddr *) &socket_address, sizeof(socket_address)) < 0) {
            perror("bind failed");
            exit(1);
        }
        return socket_fd;
    }
    int get_socket_fd() {
        return socket_fd;
    }
    void handle_connection() {
        if ((connection_socket = accept(socket_fd, (struct sockaddr *) &socket_address, (socklen_t * ) & socket_address_len)) < 0) {
            perror("accept");
            exit(EXIT_FAILURE);
        }
        inet_ntop(AF_INET, &(socket_address.sin_addr), str_addr, sizeof(str_addr));
        std::cout << protocol << ": Connection by " << str_addr << ":" << ntohs(socket_address.sin_port) << std::endl;
        read(connection_socket, buffer, 1024);
        std::cout << protocol << ": Received message: " << buffer << " from " << str_addr << ":" << ntohs(socket_address.sin_port) << std::endl;
        send(connection_socket, buffer, strlen(buffer), 0);
        std::cout << protocol << ": Connection with " << str_addr << ":" << ntohs(socket_address.sin_port) << " ended" << std::endl;
    }
};
class ServerV6 {
private:
    int socket_fd, connection_socket;
    struct sockaddr_in6 socket_address;
    int socket_address_len = sizeof(socket_address);
    char buffer[BUFFER_SIZE] = {0};
    char str_addr[INET6_ADDRSTRLEN];
    std::string protocol;
public:
    ServerV6(std::string protocol_name="IPv6") {
        protocol = protocol_name;
        socket_fd = setup_socket();
        // Listen
        if (listen(socket_fd, 3) < 0) {
            perror("listen");
            exit(EXIT_FAILURE);
        }
        std::cout << protocol << ": Opened socket connection" << std::endl;
    }
    int setup_socket() {
        // Create socket file descriptor
        if ((socket_fd = socket(AF_INET6, SOCK_STREAM, IPPROTO_TCP)) == -1) {
            perror("socket failed");
            exit(EXIT_FAILURE);
        }

        int opt = 1;
        int v6_only = 1;
        setsockopt(socket_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
        setsockopt(socket_fd, IPPROTO_IPV6, IPV6_V6ONLY, &v6_only, sizeof(int));

        // Setup socket
        memset((char *) &socket_address, 0, sizeof(socket_address));
        socket_address.sin6_family = AF_INET6;
        socket_address.sin6_port = htons(PORT_V6);
        inet_ntop(AF_INET, &(socket_address.sin6_addr), ADDRESS_V6, sizeof(ADDRESS_V6));

        // Bind socket to address
        if (bind(socket_fd, (struct sockaddr *) &socket_address, sizeof(socket_address)) < 0) {
            perror("bind failed");
            exit(1);
        }
        return socket_fd;
    }
    int get_socket_fd() {
        return socket_fd;
    }
    void handle_connection() {
        if ((connection_socket = accept(socket_fd, (struct sockaddr *) &socket_address, (socklen_t * ) & socket_address_len)) < 0) {
            perror("accept");
            exit(EXIT_FAILURE);
        }
        inet_ntop(AF_INET6, &(socket_address.sin6_addr), str_addr, sizeof(str_addr));
        std::cout << protocol << ": Connection by " << str_addr << ":" << ntohs(socket_address.sin6_port) << std::endl;
        read(connection_socket, buffer, 1024);
        std::cout << protocol << ": Received message: " << buffer << " from " << str_addr << ":" << ntohs(socket_address.sin6_port) << std::endl;
        send(connection_socket, buffer, strlen(buffer), 0);
        std::cout << protocol << ": Connection with " << str_addr << ":" << ntohs(socket_address.sin6_port) << " ended" << std::endl;
    }
};

bool sigint_catcher = false;
void sigint_handler(int param) {
    sigint_catcher = true;
    printf("\nUser pressed Ctrl+C\n");
    // exit(1); // we're not using it since we want to exit the main loop and free resources there.
}

int main() {
    signal(SIGINT, sigint_handler);

    Server server = Server();
    ServerV6 serverV6 = ServerV6();

    fd_set socket_fds; // socket file descriptors

    while (!sigint_catcher)
    {
        int sock_v4_fd = server.get_socket_fd();
        int sock_v6_fd = serverV6.get_socket_fd();

        FD_ZERO(&socket_fds);
        FD_SET(sock_v4_fd, &socket_fds);
        FD_SET(sock_v6_fd, &socket_fds);

        int fd_max = std::max(sock_v6_fd, sock_v4_fd);

        timeval interval;
        interval.tv_sec = 1;

        int retval = select(fd_max + 1, &socket_fds, nullptr, nullptr, &interval);
//        printf("retval: %d\n", retval);
        if (retval == -1)
        {   // happens usually when select() fails. For some reason, it also happens after SIGINT, even with our custom SIGINT handler.
            printf("Select failed.");
            continue;
        }
        else if (retval == 0)
        {
//            printf("Timeout - no incoming connections. Time to check if SIGINT arrived.\n");
        }
        else
        {
            if (FD_ISSET(sock_v4_fd, &socket_fds))
            {
                server.handle_connection();
            }
            else if (FD_ISSET(sock_v6_fd, &socket_fds))
            {
                serverV6.handle_connection();
            }
            else
            {
                printf("That's kinda unexpected\n");
            }
        }
    }
    // ##########################################
    // # Here we need to free sockets and stuff #
    // ##########################################
    return 0;
}