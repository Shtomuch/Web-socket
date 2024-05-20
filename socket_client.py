import socket


def main():
    host = socket.gethostname()
    port = 5000

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.connect((host, port))
    message = input('>>> ')

    while message.lower().strip() != 'quit':
        client_socket.send(message.encode())
        msg = client_socket.recv(1024).decode()
        print(f"Received by: {msg}")
        message = input(">>> ")

    client_socket.close()


if __name__ == '__main__':
    main()
