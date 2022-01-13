# Nazwa projektu: System niezawodnego strumieniowania danych po UDP
# Autorzy:        Michał Matak, Paweł Müller, Jakub Robaczewski, Grzegorz Rusinek
# Data:           14.01.2022

# Default client configuration
SERVER_NOT_RESPONDING_TIMEOUT = 60  # After this time client will close connection
CLIENT_ACK_TIMEOUT = 0.5            # How much time server has for process confirmation (ACK)

# Default server configuration
CLIENT_NOT_RESPONDING_TIMEOUT = 60  # After this time server will close connection
NEXT_MESSAGE_TIMEOUT = 15           # How much time there is for new message to show up
SERVER_ACK_TIMEOUT = 0.01           # How much time client has for confirmation (ACK)
