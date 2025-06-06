import socket
carsteer =0.0
caraccel =1.0



# --- UDP Server Setup ---
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('127.0.0.1', 65432)
server_socket.bind(server_address)

receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver_address = ('127.0.0.2', 65433)
# receiver_socket.bind(receiver_address)



print("UDP server is listening on", server_address)


def send_udp_message(carsteer: float, caraccel: float, host: str = '127.0.0.2', port: int = 65433):
    message = f"{carsteer},{caraccel}"


    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.sendto(message.encode(), (host, port))


# --- Main Server Loop ---
try:
    while True:
        data, client_address = server_socket.recvfrom(1024)
        car_state = data.decode()
        print(car_state)

        send_udp_message(0.0,1.0)
finally:
    server_socket.close()
    print("UDP server closed.")


