#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>

#define PORT 8888

struct sockaddr_in server_address;
int socket_file_descriptor;

void send_message(char *message);
void prepare_client();


int main() {
    prepare_client();
    char message[100] = "";

    for (int i = 0; i < 5; i++) {
        sprintf(message, "Message no. %d.", i);
        send_message(message);
    }
    printf("Client finished its job.");
}

void prepare_client() {
    // Creating socket file descriptor
    if ((socket_file_descriptor = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("Socket creation failed");
        exit(EXIT_FAILURE);
    }

    memset(&server_address, 0, sizeof(server_address));

    // Configuring server
    server_address.sin_family = AF_INET;
    server_address.sin_port = htons(PORT);
    server_address.sin_addr.s_addr = INADDR_ANY;
}


void send_message(char *message) {
    sendto(
            socket_file_descriptor,
            (const char *) message,
            strlen(message),
            0,
            (const struct sockaddr *) &server_address,
            sizeof(server_address)
    );
}
