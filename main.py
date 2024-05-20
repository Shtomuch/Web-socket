import json
from datetime import datetime
import logging
import mimetypes
import socket
from threading import Thread
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

BASE_DIR = Path()
BUFFER_SIZE = 1024
HTTP_PORT = 3000
HTTP_HOST = '0.0.0.0'
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5000
STORAGE_DIR = BASE_DIR / 'storage'
STORAGE_FILE = STORAGE_DIR / 'data.json'


http_logger = logging.getLogger('http_logger')
socket_logger = logging.getLogger('socket_logger')

http_handler = logging.FileHandler('http_server.log')
socket_handler = logging.FileHandler('socket_server.log')

http_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
socket_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

http_handler.setFormatter(http_formatter)
socket_handler.setFormatter(socket_formatter)

http_logger.addHandler(http_handler)
socket_logger.addHandler(socket_handler)

http_logger.setLevel(logging.DEBUG)
socket_logger.setLevel(logging.DEBUG)


class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        size = int(self.headers['Content-Length'])
        data = self.rfile.read(size)

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()

        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()
        http_logger.info(f"Received POST request with data: {data}")

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        match pr_url.path:
            case "/":
                self.send_html_file(".index.html")
            case "/message":
                self.send_html_file("message.html")
            case _:
                file = BASE_DIR.joinpath(pr_url.path[1:])
                if file.exists():
                    self.send_static()
                else:
                    self.send_html_file("error.html", 404)
        http_logger.info(f"Handled GET request for path: {self.path}")

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(BASE_DIR / filename, 'rb') as fd:
            self.wfile.write(fd.read())
        http_logger.info(f"Sent HTML file: {filename} with status: {status}")

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(BASE_DIR / self.path[1:], 'rb') as file:
            self.wfile.write(file.read())
        http_logger.info(f"Sent static file: {self.path}")


def save_data_from_form(data):
    data_parse = urllib.parse.unquote_plus(data.decode())
    socket_logger.info(f"Received data to save: {data_parse}")
    try:
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}

        if STORAGE_FILE.exists():
            try:
                with open(STORAGE_FILE, 'r', encoding='utf-8') as file:
                    existing_data = json.load(file)
            except json.JSONDecodeError:
                socket_logger.error('JSONDecodeError')
                existing_data = {}
        else:
            existing_data = {}

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        existing_data[timestamp] = data_dict

        with open(STORAGE_FILE, 'w', encoding='utf-8') as file:
            json.dump(existing_data, file, ensure_ascii=False, indent=4)
        socket_logger.info(f"Data saved successfully: {data_dict}")
    except ValueError as err:
        socket_logger.error(err)
    except OSError as err:
        socket_logger.error(err)


def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    socket_logger.info(f"Started socket server on {host}:{port}")
    try:
        while True:
            msg, client_address = server_socket.recvfrom(BUFFER_SIZE)
            socket_logger.info(f"Received message from {client_address}: {msg}")
            save_data_from_form(msg)
    except KeyboardInterrupt:
        pass
    finally:
        server_socket.close()
        socket_logger.info("Socket server stopped")


def run_http_server(host, port):
    address = (host, port)
    http_server = HTTPServer(address, HttpHandler)
    http_logger.info(f"Started HTTP server on {host}:{port}")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()
        http_logger.info("HTTP server stopped")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

    server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
    server.start()

    socket_server = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    socket_server.start()
