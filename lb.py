import socket
import threading
import time
import argparse

parser = argparse.ArgumentParser(description="Layer 7 Load Balancer")
parser.add_argument("--health-check-interval", type=int, default=10, help="Seconds between health checks")
parser.add_argument("--health-check-url", type=str, default='/', help="URL path to health check")
args = parser.parse_args()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

HOST = '127.0.0.1'
PORT = 8080

BACKENDS = [ # Change to list of dicts +++++++++
    {'address': ('127.0.0.1', 8081), 'healthy': True},
    {'address': ('127.0.0.1', 8082), 'healthy': True}
]

current_index = 0
lock = threading.Lock()

def health_check_worker(interval, url):
    request = f"GET {url} HTTP/1.1\r\nHost: localhost\r\n\r\n".encode('utf-8')

    while True:
        for backend in BACKENDS:
            address = backend['address']

            try:
                healthcheck_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                healthcheck_socket.settimeout(2)
                healthcheck_socket.connect(address)
                healthcheck_socket.send(request)
                response = healthcheck_socket.recv(1024).decode('utf-8')

                #print(f"DEBUG response from {address}: {repr(response)}")

                if '200 OK' in response:
                    backend['healthy'] = True
                    print(f"Backend {address} is healthy.")
                else:
                    backend['healthy'] = False
                    print(f"Backend {address} returned bad status.")
            
            except (ConnectionRefusedError, socket.timeout, OSError):
                backend['healthy'] = False
                print(f"Backend {address} is DOWN.")

            finally:
                healthcheck_socket.close()

        time.sleep(interval)

def get_next_backend():
    global current_index

    with lock:
        for _ in range(len(BACKENDS)):
            backend = BACKENDS[current_index]
            if backend['healthy']:
                current_index = (current_index + 1) % len(BACKENDS)
                return backend['address']
            else:
                current_index = (current_index + 1) % len(BACKENDS)

        return None

server_socket.bind((HOST, PORT))

server_socket.listen(5)
print(f"Server is listening on {HOST}: {PORT}...")

def handle_client(client_socket, client_address):
    raw_data = client_socket.recv(1024)

    decoded_data = raw_data.decode('utf-8')
    print("Received data:")
    print(decoded_data)

    backend_address = get_next_backend()
    if backend_address is None:
        error_response = b"HTTP/1.1 503 Service Unavailable\r\n\r\nNo backends available."
        client_socket.sendall(error_response)
        client_socket.close()
        return
    
    backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    backend_socket.connect(backend_address)
    backend_socket.send(raw_data)

    while True:
        chunk = backend_socket.recv(4096)

        if not chunk:
            break

        client_socket.sendall(chunk)
        print(f"Backend says: {chunk}")

    backend_socket.close()

    client_socket.close()
    print("Client connection closed")

health_thread = threading.Thread(
    target=health_check_worker,
    args=(args.health_check_interval, args.health_check_url),
    daemon=True
)
health_thread.start()

while True:
    try:
        client_socket, client_adress = server_socket.accept()
        print(f"Connection accepted from client at: {client_adress}")

        thread = threading.Thread(target=handle_client, args=(client_socket, client_adress))

        thread.start()
    except Exception as e:
        print(f"An error ocurred: {e}")




