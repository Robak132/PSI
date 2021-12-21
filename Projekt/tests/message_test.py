from src.message import DataMessage, Message, ACKMessage, MessageType


class TestMessage:
    def test_verify_data(self):
        full_fragment = "1" * 400
        fragment = full_fragment.encode("utf-8")
        message = DataMessage(0, fragment).pack()
        recv_message = Message.unpack(message)
        recv_fragment = recv_message.data.decode("utf-8")
        assert recv_fragment == full_fragment

    def test_ack(self):
        test_string = b"TEST"
        message = DataMessage(1, test_string).pack()

        recv_message = Message.unpack(message)
        assert recv_message.message_type == MessageType.MSG
        assert recv_message.data == test_string
        assert recv_message.identifier == 1
        ack_message = ACKMessage(recv_message.identifier).pack()

        recv_ack_message = Message.unpack(ack_message)
        assert recv_ack_message.message_type == MessageType.ACK
        assert recv_ack_message.identifier == 1
