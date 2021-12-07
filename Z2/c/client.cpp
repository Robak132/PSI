#include <arpa/inet.h>
#include <netinet/in.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <sys/socket.h>
#include <unistd.h>
#include <string>
#include <iostream>
#include <fcntl.h>

#define ADDRESS_V4 "127.0.0.1"
#define ADDRESS_V6 "::1"
#define PORT 8888

class Client {
private:
    struct sockaddr_in serv_address{};
protected:
    int sock = 0;
    const char* protocol;
    const char* address;
    int port;
public:
    Client(const char* _address, int _port, const char* protocol_name="IPv4") {
        address = _address;
        port = _port;
        protocol = protocol_name;
    }
    virtual void prepare() {
        if ((sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) < 0) {
            printf("\n Socket creation error \n");
            exit(EXIT_FAILURE);
        }

        memset((char *) &serv_address, 0, sizeof(serv_address));
        serv_address.sin_family = AF_INET;
        serv_address.sin_port = htons(port);

        // Convert IPv4 and IPv6 addresses from text to binary form
        if (inet_pton(AF_INET, address, &serv_address.sin_addr) <= 0) {
            printf("\nInvalid address/ Address not supported \n");
            exit(EXIT_FAILURE);
        }

        // Set non-blocking
        fcntl(sock, F_SETFL, fcntl(sock, F_GETFL, NULL) | O_NONBLOCK);

        std::cout << protocol << ": Trying to connect with: " << address << ":" << port << std::endl;

        // Trying to connect with timeout
        while (connect(sock, (struct sockaddr *) &serv_address, sizeof(serv_address)) < 0) {
            if (errno == EINPROGRESS) {
                struct timeval tv{};
                fd_set timeout_set;

                tv.tv_sec = 10;
                tv.tv_usec = 0;

                FD_ZERO(&timeout_set);
                FD_SET(sock, &timeout_set);
                if (select(sock + 1, nullptr, &timeout_set, nullptr, &tv) == 0) {
                    std::cout << protocol << ": Connection timeout" << std::endl;
                    exit(0);
                }
            } else {
                std::cout << protocol << ": Connection refused" << std::endl;
                break;
            }
        }

        // Set blocking
        fcntl(sock, F_SETFL, fcntl(sock, F_GETFL, NULL) & (~O_NONBLOCK));
    }
    void send_message(std::string str_message) const {
        std::cout << protocol << ": Sending message: " << str_message << std::endl;
        char *message = &str_message[0];
        send(sock, message, strlen(message), 0);
    }
};
class ClientV6 : public Client {
private:
    struct sockaddr_in6 serv_address{};
public:
    ClientV6(const char* _address, int _port, const char* protocol_name="IPv6") : Client(_address, _port, protocol_name) {
         protocol = protocol_name;
         address = _address;
         port = _port;
    }
    void prepare() override {
        if ((sock = socket(AF_INET6, SOCK_STREAM, IPPROTO_TCP)) < 0) {
            printf("\n Socket creation error \n");
            exit(EXIT_FAILURE);
        }

        memset((char *) &serv_address, 0, sizeof(serv_address));
        serv_address.sin6_family = AF_INET6;
        serv_address.sin6_port = htons(port);

        // Convert IPv4 and IPv6 addresses from text to binary form
        if (inet_pton(AF_INET6, address, &serv_address.sin6_addr) <= 0) {
            printf("\nInvalid address/ Address not supported \n");
            exit(EXIT_FAILURE);
        }

        // Set non-blocking
        fcntl(sock, F_SETFL, fcntl(sock, F_GETFL, NULL) | O_NONBLOCK);

        std::cout << protocol << ": Trying to connect with: " << address << ":" << port << std::endl;

        // Trying to connect with timeout
        while (connect(sock, (struct sockaddr *) &serv_address, sizeof(serv_address)) < 0) {
            if (errno == EINPROGRESS) {
                struct timeval tv{};
                fd_set timeout_set;

                tv.tv_sec = 10;
                tv.tv_usec = 0;

                FD_ZERO(&timeout_set);
                FD_SET(sock, &timeout_set);
                if (select(sock + 1, nullptr, &timeout_set, nullptr, &tv) == 0) {
                    std::cout << protocol << ": Timeout" << std::endl;
                    exit(0);
                }
            } else {
                std::cout << protocol << ": Connection refused" << std::endl;
                break;
            }
        }

        // Set blocking
        fcntl(sock, F_SETFL, fcntl(sock, F_GETFL, NULL) & (~O_NONBLOCK));
    }
};

int main() {
    Client client = Client(ADDRESS_V4, PORT);
    client.prepare();
    client.send_message(std::string(500, '1') + std::string(500, '2'));

    ClientV6 clientV6 = ClientV6(ADDRESS_V6, PORT);
    clientV6.prepare();
    clientV6.send_message(std::string(500, '3') + std::string(500, '4'));

    Client client2 = Client("10.0.0.0", PORT);
    client2.prepare();
    return 0;
}
