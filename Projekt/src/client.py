import logging
import signal
import socket
from time import sleep
from decorators import thread_request
from message import Message, RequestMessage, ACKMessage, QuitMessage, MessageType, ErrorType
from common import setup_loggers, receive_message, send_message, setup_sockets_ipv4, setup_sockets_ipv6
import CONFIG as CFG


class ClientV4:
    def __init__(self,
                 receive_address: tuple[str, int] = ("", 0),
                 send_address: tuple[str, int] = ("", 0),
                 buffer_size: int = 448,
                 logging_level: int = logging.INFO):
        self.logger = setup_loggers(logging_level)
        self.setup_exit_handler()

        self.SERVER_NOT_RESPONDING_TIMEOUT = CFG.SERVER_NOT_RESPONDING_TIMEOUT
        self.CLIENT_ACK_TIMEOUT = CFG.CLIENT_ACK_TIMEOUT
        self.server_lag = 0

        self.receive_socket, self.send_socket = self.setup_sockets(receive_address, send_address)
        self.receive_port = self.receive_socket.getsockname()[1]

        self.buffer_size = buffer_size
        self.target_ip = None
        self.ack_port = None
        self.is_running = True

    def setup_sockets(self, receive_address, send_address):
        return setup_sockets_ipv4(receive_address, self.CLIENT_ACK_TIMEOUT, send_address)

    def setup_exit_handler(self):
        signal.signal(signal.SIGINT, lambda sig, frame: self.stop())

    def stop(self):
        self.is_running = False

    def receive(self, max_messages: int = None):
        result = b""
        pkg_number = 0
        data_pkg_number = 0
        while self.is_running:
            try:
                while True:
                    message = self.receive_message()
                    if message.message_type == MessageType.FIN:
                        self.logger.info("Transmission ended")
                        self.is_running = False
                        break
                    elif message.message_type == MessageType.ERR:
                        self.logger.error(f"{ErrorType(message.identifier).name}")
                        self.is_running = False
                        break
                    elif message.message_type == MessageType.INF:
                        ack_port = message.data_to_int()
                        if self.ack_port != ack_port:
                            self.ack_port = ack_port
                            self.logger.info(f'Sending ACKs to: {ack_port}')
                    elif message.identifier == pkg_number + 1 and message.message_type == MessageType.MSG and message.check_hash():
                        pkg_number += 1
                        self.server_lag = 0
                        if message.size != 0:
                            data_pkg_number += 1
                            result += message.data
                            if data_pkg_number == max_messages:
                                self.logger.info(f'Limit of received packages reached. Ending transmission.')
                                self.is_running = False
            except socket.timeout:
                self.server_lag = self.server_lag + self.CLIENT_ACK_TIMEOUT
                if self.server_lag >= self.SERVER_NOT_RESPONDING_TIMEOUT:
                    self.logger.info("Server not responding: timeout")
                    self.is_running = False

            if self.ack_port is not None:
                self.send_message(ACKMessage(pkg_number), (self.target_ip, self.ack_port))

        if not self.is_running and self.target_ip and self.ack_port:
            # Client is closing connection
            self.send_message(QuitMessage(1), (self.target_ip, self.ack_port))
        return result

    def receive_message(self) -> Message:
        message, _ = receive_message(self.receive_socket, self.buffer_size, self.logger)
        return message

    def send_message(self, message: Message, target: tuple[str, int]):
        send_message(self.send_socket, message, target, self.logger)

    def request(self, stream: int, target: tuple[str, int], thread: bool = False, max_messages: int = None):
        if thread:
            return self.request_nonblocking(stream, target, max_messages)
        else:
            return self.request_blocking(stream, target, max_messages)

    def request_blocking(self, stream: int, target: tuple[str, int], max_messages: int = None):
        self.target_ip, _ = target
        self.send_message(RequestMessage(stream, self.receive_port), target)
        return self.receive(max_messages)

    @thread_request
    def request_nonblocking(self, stream: int, target: tuple[str, int], max_messages: int = None):
        return self.request_blocking(stream, target, max_messages)


class ClientV6(ClientV4):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def setup_sockets(self, receive_address, send_address):
        return setup_sockets_ipv6(receive_address, self.CLIENT_ACK_TIMEOUT, send_address)


class ClientV4WithLag(ClientV4):
    def __init__(self, lag: float = 0, **kwargs):
        super().__init__(**kwargs)
        self.lag = lag

    def receive_message(self) -> Message:
        sleep(self.lag)
        return super().receive_message()

    def send_message(self, message: Message, target: tuple[str, int]):
        sleep(self.lag)
        super().send_message(message, target)


if __name__ == '__main__':
    client = ClientV4(logging_level=logging.DEBUG)
    data = client.request(stream=1, target=("127.0.0.1", 8801))
    # print(data.decode("utf-8"))
