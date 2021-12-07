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
#include <fcntl.h>

#define ADDRESS_V4 "127.0.0.1"
#define PORT_V4 8888

#define ADDRESS_V6 "::1"
#define PORT_V6 8888

#define BUFFER_SIZE 100

class Server {
private:
    struct sockaddr_in socket_address{};
    int socket_address_len = sizeof(socket_address);
protected:
    int socket_fd{};
    char buffer[BUFFER_SIZE+1] = {0};
    std::string protocol;
public:
    explicit Server(std::string protocol_name="IPv4") {
        protocol = protocol_name;
    }
    virtual void prepare() {
        // Create socket file descriptor
        if ((socket_fd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) == 0) {
            perror("socket failed");
            exit(EXIT_FAILURE);
        }

        // Set non-blocking
        fcntl(socket_fd, F_SETFL, fcntl(socket_fd, F_GETFL, NULL) | O_NONBLOCK);

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

        // Listen
        if (listen(socket_fd, 3) < 0) {
            perror("listen");
            exit(EXIT_FAILURE);
        }
        set_socket_fd(socket_fd);
        std::cout << protocol << ": Opened socket connection" << std::endl;
    }
    virtual void accept_connection() {
        int connection_socket;
        if ((connection_socket = accept(socket_fd, (struct sockaddr *) &socket_address, (socklen_t * ) & socket_address_len)) < 0) {
            perror("accept");
            exit(EXIT_FAILURE);
        }
        receive_connection(connection_socket);
    }
    virtual void receive_connection(int connection_socket) {
        char address[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &(socket_address.sin_addr), address, sizeof(address));
        int port = ntohs(socket_address.sin_port);

        std::cout << protocol << ": Connection by " << address << ":" << port << std::endl;
        while ((recv(connection_socket, buffer, BUFFER_SIZE, 0)) > 0) {
            std::cout << protocol << ": Received message: " << buffer << " from " << address << ":" << port << std::endl;
        }
        close(connection_socket);
        std::cout << protocol << ": Connection with " << address << ":" << port << " ended" << std::endl;
    }

    void set_socket_fd(int _socket_fd) {
        socket_fd = _socket_fd;
    }
    int get_socket_fd() const {
        return socket_fd;
    }
};
class ServerV6 : public Server {
private:
    struct sockaddr_in6 socket_address{};
    int socket_address_len = sizeof(socket_address);
public:
    explicit ServerV6(std::string protocol_name="IPv6") : Server() {
        protocol = protocol_name;
    }
    void prepare() override {
        int socket_fd;

        // Create socket file descriptor
        if ((socket_fd = socket(AF_INET6, SOCK_STREAM, IPPROTO_TCP)) == -1) {
            perror("socket failed");
            exit(EXIT_FAILURE);
        }

        // Set options
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

        // Listen
        if (listen(socket_fd, 3) < 0) {
            perror("listen");
            exit(EXIT_FAILURE);
        }

        set_socket_fd(socket_fd);
        std::cout << protocol << ": Opened socket connection" << std::endl;
    }
    void receive_connection(int connection_socket) override {
        char address[INET6_ADDRSTRLEN];
        inet_ntop(AF_INET6, &(socket_address.sin6_addr), address, sizeof(address));
        int port = ntohs(socket_address.sin6_port);

        std::cout << protocol << ": Connection by " << address << ":" << port << std::endl;
        while ((recv(connection_socket, buffer, BUFFER_SIZE, 0)) > 0) {
            std::cout << protocol << ": Received message: " << buffer << " from " << address << ":" << port << std::endl;
        }
        close(connection_socket);
        std::cout << protocol << ": Connection with " << address << ":" << port << " ended" << std::endl;
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
    server.prepare();
    ServerV6 serverV6 = ServerV6();
    serverV6.prepare();

    fd_set socket_fds; // socket file descriptors

    while (!sigint_catcher) {
        int sock_v4_fd = server.get_socket_fd();
        int sock_v6_fd = serverV6.get_socket_fd();

        FD_ZERO(&socket_fds);
        FD_SET(sock_v4_fd, &socket_fds);
        FD_SET(sock_v6_fd, &socket_fds);

        int fd_max = std::max(sock_v6_fd, sock_v4_fd);

        struct timeval interval{};
        interval.tv_sec = 10;

        int retval = select(fd_max + 1, &socket_fds, nullptr, nullptr, &interval);
        if (retval == -1) {
            // happens usually when select() fails. For some reason, it also happens after SIGINT, even with our custom SIGINT handler.
            printf("Select failed.");
            continue;
        }
        else if (retval == 0) {
            printf("No incoming connections. Server timeout.\n");
            exit(0);
        }
        else {
            if (FD_ISSET(sock_v4_fd, &socket_fds)) {
                server.accept_connection();
            }
            else if (FD_ISSET(sock_v6_fd, &socket_fds)) {
                serverV6.accept_connection();
            }
        }
    }
    return 0;
}
