// Server side C/C++ program to demonstrate Socket programming
#include <unistd.h>
#include <stdio.h>
#include <sys/socket.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <string>
#include <string.h>
#include <iostream>
#include <sstream>

#define ADDRESS_V4 "127.0.0.1"
#define PORT_V4 8888
#define PORT_V6 8888
#define BUFFER_SIZE 102400

class Server {
private:
    int server_fd, new_socket, valread;
    struct sockaddr_in socket_address;
    int socket_address_len = sizeof(socket_address);
    char buffer[BUFFER_SIZE] = {0};
    std::string protocol;
public:
    Server(std::string protocol_name="IPv4") {
        protocol = protocol_name;
        server_fd = setup_socket();
        // Listen
        if (listen(server_fd, 3) < 0) {
            perror("listen");
            exit(EXIT_FAILURE);
        }
        std::cout << protocol << ": Opened socket connection" << std::endl;
    }
    int setup_socket() {
        int server_fd;
        // Create socket file descriptor
        if ((server_fd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) == 0) {
            perror("socket failed");
            exit(EXIT_FAILURE);
        }

        // Setup socket
        memset((char *) &socket_address, 0, sizeof(socket_address));
        socket_address.sin_family = AF_INET;
        socket_address.sin_addr.s_addr = inet_addr(ADDRESS_V4);
        socket_address.sin_port = htons(PORT_V4);

        int opt = 1;
        if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt))) {
            perror("setsockopt");
            exit(EXIT_FAILURE);
        }

        // Bind socket to address
        if (bind(server_fd, (struct sockaddr *) &socket_address, sizeof(socket_address)) < 0) {
            perror("bind failed");
            exit(1);
        }
        return server_fd;
    }
    void run() {
        while (true) {
            if ((new_socket = accept(server_fd, (struct sockaddr *) &socket_address, (socklen_t * ) & socket_address_len)) < 0) {
                perror("accept");
                exit(EXIT_FAILURE);
            }
            inet_ntop(AF_INET6, &(socket_address.sin6_addr), str_addr, sizeof(str_addr));
            std::cout << protocol << ": Connection by " << str_addr << ":" << ntohs(socket_address.sin6_port) << std::endl;
            read_successfull = read(new_socket, buffer, 1024);
            std::cout << protocol << ": Received message: " << buffer << " from" << str_addr << ":" << ntohs(socket_address.sin6_port) << std::endl;
            send(new_socket, buffer, strlen(buffer), 0);
            std::cout << protocol << ": Connection with " << str_addr << ":" << ntohs(socket_address.sin6_port) << " ended" << std::endl;
        }
    }
};
class ServerV6 {
private:
    int server_fd, new_socket, read_successfull;
    struct sockaddr_in6 socket_address;
    int socket_address_len = sizeof(socket_address);
    char buffer[BUFFER_SIZE] = {0};
    char str_addr[INET6_ADDRSTRLEN];
    std::string protocol;
public:
    ServerV6(std::string protocol_name="IPv6") {
        protocol = protocol_name;
        server_fd = setup_socket();
        // Listen
        if (listen(server_fd, 3) < 0) {
            perror("listen");
            exit(EXIT_FAILURE);
        }
        std::cout << protocol << ": Opened socket connection" << std::endl;
    }
    int setup_socket() {
        int server_fd;
        // Create socket file descriptor
        if ((server_fd = socket(AF_INET6, SOCK_STREAM, IPPROTO_TCP)) == -1) {
            perror("socket failed");
            exit(EXIT_FAILURE);
        }

        int opt = 1;
        int v6_only = 1;
        setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
        setsockopt(server_fd, IPPROTO_IPV6, IPV6_V6ONLY, &v6_only, sizeof(int));

        // Setup socket
        memset((char *) &socket_address, 0, sizeof(socket_address));
        socket_address.sin6_family = AF_INET6;
        socket_address.sin6_addr = in6addr_any;
        socket_address.sin6_port = htons(PORT_V6);

        // Bind socket to address
        if (bind(server_fd, (struct sockaddr *) &socket_address, sizeof(socket_address)) < 0) {
            perror("bind failed");
            exit(1);
        }
        return server_fd;
    }
    void run() {
        while (true) {
            if ((new_socket = accept(server_fd, (struct sockaddr *) &socket_address, (socklen_t * ) & socket_address_len)) < 0) {
                perror("accept");
                exit(EXIT_FAILURE);
            }
            inet_ntop(AF_INET6, &(socket_address.sin6_addr), str_addr, sizeof(str_addr));
            std::cout << protocol << ": Connection by " << str_addr << ":" << ntohs(socket_address.sin6_port) << std::endl;
            read_successfull = read(new_socket, buffer, 1024);
            std::cout << protocol << ": Received message: " << buffer << " from" << str_addr << ":" << ntohs(socket_address.sin6_port) << std::endl;
            send(new_socket, buffer, strlen(buffer), 0);
            std::cout << protocol << ": Connection with " << str_addr << ":" << ntohs(socket_address.sin6_port) << " ended" << std::endl;
        }
    }
};


int main() {
//    Server server = Server();
//    server.run();
//    ServerV6 serverV6 = ServerV6();
//    serverV6.run();
    return 0;
}