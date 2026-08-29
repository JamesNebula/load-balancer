# HTTP Load Balancer

This project handles raw TCP socket connections, parses and forwards HTTP requests, distributes traffic across multiple backend servers using round-robin scheduling, and continuously monitors backend health to ensure zero-downtime request routing.

## Features
- Distributes incoming HTTP requests across a pool of backend servers
- Round-robin scheduling algorithm for even traffic distribution
- Thread-safe request routing using mutex locks
- Concurrent client handling with multi-threading
- Automated periodic health checks on all backend servers
- Automatic failover: removes unhealthy servers from the pool in real time
- Automatic recovery: re-adds servers once they pass health checks again
- Returns HTTP 503 Service Unavailable when all backends are down
- Configurable health check interval and URL via command-line arguments

## How it works
The load balancer operates as a TCP proxy between clients and backend servers:
- **Listening**: The load balancer binds to a port and listens for incoming TCP connections
- **Concurrency**: Each client connection is handed off to a dedicated worker thread
- **Routing**: A thread-safe round-robin algorithm selects the next healthy backend server
- **Forwarding**: The raw HTTP request is forwarded to the selected backend
- **Streaming**: The backend response is read in chunks and streamed back to the client
- **Health checking**: A background daemon thread periodically sends HTTP GET requests to each backend. Servers returning 200 OK are marked healthy, servers that fail or time out are removed from the pool.

## Usage
Start the load balancer:   
`python lb.py`  

With custom health check settings:  
`python lb.py --health-check-interval 5 --health-check-url /health`  

Start backend servers in separate terminals (using pythons built in HTTP server for testing)  
`python3 -m http.server 8081`    
`python3 -m http.server 8082`  

Test with curl:  
`curl http://localhost:8080/`   
 
Test with concurrent requests:  
`curl --parallel --parallel-immediate --parallel-max 10 --config urls.txt`   
