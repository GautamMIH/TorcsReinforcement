import socket

# Create a UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind to localhost and a port
server_address = ('127.0.0.1', 65432)
server_socket.bind(server_address)

print("UDP server is listening on", server_address)

try:
    while True:
        # Receive data from client (data, address)
        data, client_address = server_socket.recvfrom(1024)
        print(data.decode())

        # Send acknowledgment back to client
        server_socket.sendto(b"ACK", client_address)
finally:
    server_socket.close()
    print("UDP server closed.")
