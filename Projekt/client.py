import socket
import time
from message import Message


class Client:
    def __init__(self):
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket.bind(("127.0.0.1", 9900))
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.bind(("127.0.0.1", 9999))
        self.protocol = "IPv4"

    def receive(self):
        full_data = b""
        pkg_number = 0
        while True:
            binary_data = self.recv_socket.recv(10240)
            if binary_data == b"END":
                break
            else:
                message = Message.unpack(binary_data, len(binary_data))
                print(f'received: {message.message_type}')
                if message.message_type.decode('utf-8').startswith('MSG'):
                    print(int(str.strip(message.message_type[3:].decode('utf-8'))))
                    if int(str.strip(message.message_type[3:].decode('utf-8'))) == pkg_number + 1:
                        pkg_number += 1
                full_data += message.data
                # print(message.data.decode('utf-8')) # na 32 pakiecie Pana Tadeusza po 121 bajtow spada z rowerka
            # time.sleep(1)
            print(f"Sending ACK {pkg_number}")
            self.send_socket.sendto(b"ACK" + bytes(str(pkg_number), 'utf-8'), ("127.0.0.1", 8800))
        print(full_data.decode('utf-8'))

    def send_message(self, message: bytes):
        self.send_socket.sendto(message, ("127.0.0.1", 8800))

    def request(self):
        self.send_message(Message(b"REQUEST").pack())
        self.receive()


if __name__ == '__main__':
    client = Client()
    client.request()
