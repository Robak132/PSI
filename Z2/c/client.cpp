#include <arpa/inet.h>
#include <netinet/in.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <sys/socket.h>
#include <unistd.h>
#include <string>
#include <iostream>

#define ADDRESS_V4 "127.0.0.1"
#define ADDRESS_V6 "::1"
#define PORT 8888

class Client {
private:
    struct sockaddr_in serv_addr{};
protected:
    int sock = 0;
    std::string protocol;
public:
    explicit Client(std::string protocol_name="IPv4") {
        protocol = protocol_name;
    }
    virtual void prepare() {
        if ((sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) < 0) {
            printf("\n Socket creation error \n");
            exit(EXIT_FAILURE);
        }

        serv_addr.sin_family = AF_INET;
        serv_addr.sin_port = htons(PORT);

        // Convert IPv4 and IPv6 addresses from text to binary form
        if (inet_pton(AF_INET, ADDRESS_V4, &serv_addr.sin_addr) <= 0) {
            printf("\nInvalid address/ Address not supported \n");
            exit(EXIT_FAILURE);
        }

        if (connect(sock, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0) {
            printf("\nConnection Failed \n");
            exit(EXIT_FAILURE);
        }
    }
    void send_message(std::string str_message) const {
        std::cout << protocol << ": Sending message: " << str_message << std::endl;
        char *message = &str_message[0];
        send(sock, message, strlen(message), 0);
    }
    void close_socket() const {
        close(sock);
    }
};
class ClientV6 : public Client {
private:
    struct sockaddr_in6 serv_addr{};
public:
    ClientV6(std::string protocol_name="IPv6") : Client() {
         protocol = protocol_name;
    }
    void prepare() override {
        if ((sock = socket(AF_INET6, SOCK_STREAM, IPPROTO_TCP)) < 0) {
            printf("\n Socket creation error \n");
            exit(EXIT_FAILURE);
        }

        memset((char *) &serv_addr, 0, sizeof(serv_addr));
        serv_addr.sin6_family = AF_INET6;
        serv_addr.sin6_port = htons(PORT);

        // Convert IPv4 and IPv6 addresses from text to binary form
        if (inet_pton(AF_INET6, ADDRESS_V6, &serv_addr.sin6_addr) <= 0) {
            printf("\nInvalid address/ Address not supported \n");
            exit(EXIT_FAILURE);
        }

        if (connect(sock, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0) {
            printf("\nConnection Failed \n");
            exit(EXIT_FAILURE);
        }
    }
};

int main() {
    Client client = Client();
    client.prepare();
    client.send_message(std::string(500, '1') + std::string(500, '2'));
    client.close_socket();

    sleep(2); // Python jest za wolny w porównaniu do C++

    ClientV6 clientV6 = ClientV6();
    clientV6.prepare();
    clientV6.send_message(std::string(500, '3') + std::string(500, '4'));
    clientV6.close_socket();
    return 0;
}
