// Client side C/C++ program to demonstrate Socket programming
#include <arpa/inet.h>
#include <netinet/in.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <sys/socket.h>
#include <unistd.h>

#define PORT 8888

class Client {
private:
    int sock = 0;
    struct sockaddr_in serv_addr;
    char const *hello = "Hello from client V4";
    char buffer[1024] = {0};
public:
    Client() {
        if ((sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) < 0) {
            printf("\n Socket creation error \n");
            exit(EXIT_FAILURE);
        }

        serv_addr.sin_family = AF_INET;
        serv_addr.sin_port = htons(PORT);

        // Convert IPv4 and IPv6 addresses from text to binary form
        if (inet_pton(AF_INET, "127.0.0.1", &serv_addr.sin_addr) <= 0) {
            printf("\nInvalid address/ Address not supported \n");
            exit(EXIT_FAILURE);
        }

        if (connect(sock, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0) {
            printf("\nConnection Failed \n");
            exit(EXIT_FAILURE);
        }
        send(sock, hello, strlen(hello), 0);
        printf("Hello message sent\n");
        read(sock, buffer, 1024);
        printf("%s\n", buffer);
    }
};
class ClientV6 {
private:
    int sock = 0;
    struct sockaddr_in6 serv_addr;
    char const *hello = "Hello from client V6";
    char buffer[1024] = {0};
public:
    ClientV6() {
        if ((sock = socket(AF_INET6, SOCK_STREAM, IPPROTO_TCP)) < 0) {
            printf("\n Socket creation error \n");
            exit(EXIT_FAILURE);
        }

        memset((char *) &serv_addr, 0, sizeof(serv_addr));
        serv_addr.sin6_family = AF_INET6;
        serv_addr.sin6_port = htons(PORT);

        // Convert IPv4 and IPv6 addresses from text to binary form
        if (inet_pton(AF_INET6, "::1", &serv_addr.sin6_addr) <= 0) {
            printf("\nInvalid address/ Address not supported \n");
            exit(EXIT_FAILURE);
        }

        if (connect(sock, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0) {
            printf("\nConnection Failed \n");
            exit(EXIT_FAILURE);
        }
        send(sock, hello, strlen(hello), 0);
        printf("Hello message sent\n");
        read(sock, buffer, 1024);
        printf("%s\n", buffer);
    }
};

int main() {
    Client client = Client();
    ClientV6 clientV6 = ClientV6();
    return 0;
}