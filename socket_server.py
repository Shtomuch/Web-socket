import socket


def main():
    host = socket.gethostname()
    port = 5000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))

    print(f"UDP server up and listening on {host}:{port}")

    while True:
        msg, client_address = server_socket.recvfrom(1024)
        msg = msg.decode()
        if not msg:
            break

        print(f"Message from {client_address}: {msg}")

        message = input(">>> ")
        server_socket.sendto(message.encode(), client_address)


if __name__ == '__main__':
    main()
