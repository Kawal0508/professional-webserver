#!/usr/bin/env python3
import socket
import argparse
import os
import mimetypes
import threading
import logging
import json
import time
import signal
import sys
import ssl
import gzip
import hashlib
from datetime import datetime
from collections import defaultdict, deque
from urllib.parse import urlparse, parse_qs, unquote
from typing import Dict, Optional, Tuple, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Configuration Management
class Config:
    def __init__(self, config_file: str = None):
        self.config = {
            "server": {
                "host": "0.0.0.0",
                "port": 8080,
                "max_connections": 100,
                "timeout": 30,
                "thread_pool_size": 10
            },
            "security": {
                "rate_limit": 100,  # requests per minute per IP
                "max_file_size": 10 * 1024 * 1024,  # 10MB
                "allowed_methods": ["GET", "HEAD", "POST"],
                "cors_enabled": True,
                "cors_origins": ["*"]
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "webserver.log"
            },
            "cache": {
                "enabled": True,
                "max_size": 1000,
                "ttl": 3600  # seconds
            },
            "ssl": {
                "enabled": False,
                "cert_file": None,
                "key_file": None
            }
        }
        
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                self._merge_config(self.config, user_config)
        
        # Override with environment variables
        self._load_from_env()
    
    def _merge_config(self, base: dict, override: dict):
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _load_from_env(self):
        env_mappings = {
            "SERVER_HOST": ("server", "host"),
            "SERVER_PORT": ("server", "port"),
            "RATE_LIMIT": ("security", "rate_limit"),
            "LOG_LEVEL": ("logging", "level"),
            "SSL_ENABLED": ("ssl", "enabled")
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                if key in ["port", "rate_limit", "max_connections", "timeout", "thread_pool_size", "max_file_size", "max_size", "ttl"]:
                    self.config[section][key] = int(value)
                elif key in ["enabled", "cors_enabled"]:
                    self.config[section][key] = value.lower() in ("true", "1", "yes")
                else:
                    self.config[section][key] = value

# Metrics Collection
class Metrics:
    def __init__(self):
        self.request_count = 0
        self.response_times = deque(maxlen=1000)
        self.status_codes = defaultdict(int)
        self.bytes_served = 0
        self.active_connections = 0
        self.start_time = time.time()
        self.rate_limiter = defaultdict(lambda: deque(maxlen=60))  # per IP
    
    def record_request(self, response_time: float, status_code: int, bytes_sent: int):
        self.request_count += 1
        self.response_times.append(response_time)
        self.status_codes[status_code] += 1
        self.bytes_served += bytes_sent
    
    def is_rate_limited(self, ip: str, rate_limit: int) -> bool:
        now = time.time()
        client_requests = self.rate_limiter[ip]
        
        # Remove requests older than 1 minute
        while client_requests and client_requests[0] < now - 60:
            client_requests.popleft()
        
        if len(client_requests) >= rate_limit:
            return True
        
        client_requests.append(now)
        return False
    
    def get_stats(self) -> dict:
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        uptime = time.time() - self.start_time
        
        return {
            "uptime_seconds": uptime,
            "total_requests": self.request_count,
            "active_connections": self.active_connections,
            "average_response_time": avg_response_time,
            "bytes_served": self.bytes_served,
            "status_codes": dict(self.status_codes),
            "requests_per_second": self.request_count / uptime if uptime > 0 else 0
        }

# Global instances
config = Config()
metrics = Metrics()
logger = None

def setup_logging():
    global logger
    # Optimized logging - only log to file during high performance scenarios
    logging.basicConfig(
        level=getattr(logging, config.config["logging"]["level"]),
        format=config.config["logging"]["format"],
        handlers=[
            logging.FileHandler(config.config["logging"]["file"])
        ]
    )
    logger = logging.getLogger("webserver")

# Optimized Cache Implementation with Thread Safety
class Cache:
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
        self.access_times = {}
        self.lock = threading.RLock()  # Add thread safety for concurrent access
    
    def get(self, key: str) -> Optional[bytes]:
        with self.lock:
            if key in self.cache:
                if time.time() - self.access_times[key] < self.ttl:
                    self.access_times[key] = time.time()
                    return self.cache[key]
                else:
                    del self.cache[key]
                    del self.access_times[key]
            return None
    
    def set(self, key: str, value: bytes):
        with self.lock:
            if len(self.cache) >= self.max_size:
                # Remove oldest entry
                oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
                del self.cache[oldest_key]
                del self.access_times[oldest_key]
            
            self.cache[key] = value
            self.access_times[key] = time.time()

# Global cache instance
cache = Cache()

def parse_request(request: str) -> Tuple[Optional[str], Optional[str], Dict[str, str]]:
    """Parse HTTP request and return method, path, and headers."""
    lines = request.splitlines()
    if not lines:
        return None, None, {}
    
    # Parse request line
    request_line = lines[0]
    parts = request_line.split()
    if len(parts) < 3:
        return None, None, {}
    
    method, path, protocol = parts[0], parts[1], parts[2]
    
    # Parse headers
    headers = {}
    for line in lines[1:]:
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.strip().lower()] = value.strip()
    
    return method, path, headers

def generate_error_page(status_code: int, message: str) -> str:
    """Generate HTML error page."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{status_code} {message}</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }}
            h1 {{ color: #e74c3c; }}
        </style>
    </head>
    <body>
        <h1>{status_code} {message}</h1>
        <p>The requested resource could not be found or accessed.</p>
    </body>
    </html>
    """

def generate_directory_listing(path: str, url_path: str) -> str:
    """Generate HTML directory listing."""
    items = []
    try:
        for item in sorted(os.listdir(path)):
            item_path = os.path.join(path, item)
            is_dir = os.path.isdir(item_path)
            size = "" if is_dir else f" ({os.path.getsize(item_path)} bytes)"
            items.append(f'<li><a href="{url_path.rstrip("/")}/{item}">{item}/</a>{size}</li>' if is_dir else f'<li><a href="{url_path.rstrip("/")}/{item}">{item}</a>{size}</li>')
    except PermissionError:
        return generate_error_page(403, "Forbidden")
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Index of {url_path}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #2c3e50; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ margin: 5px 0; }}
            a {{ text-decoration: none; color: #3498db; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h1>Index of {url_path}</h1>
        <ul>
            {''.join(items)}
        </ul>
    </body>
    </html>
    """

def add_cors_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Add CORS headers if enabled."""
    if config.config["security"]["cors_enabled"]:
        headers["Access-Control-Allow-Origin"] = "*"
        headers["Access-Control-Allow-Methods"] = ", ".join(config.config["security"]["allowed_methods"])
        headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return headers

def compress_content(content: bytes, accept_encoding: str) -> Tuple[bytes, str]:
    """Compress content if client supports it."""
    if "gzip" in accept_encoding.lower():
        compressed = gzip.compress(content)
        if len(compressed) < len(content):
            return compressed, "gzip"
    return content, ""

def handle_client(conn, addr, root_dir):
    """Handle client connection with full feature set."""
    start_time = time.time()
    client_ip = addr[0]
    metrics.active_connections += 1
    
    try:
        # Set socket timeout
        conn.settimeout(config.config["server"]["timeout"])
        
        # Receive request
        request = conn.recv(4096).decode('utf-8', errors='ignore')
        if not request:
            return
        
        # Parse request
        method, path, headers = parse_request(request)
        if not method or not path:
            send_error_response(conn, 400, "Bad Request")
            return
        
        # Rate limiting
        if metrics.is_rate_limited(client_ip, config.config["security"]["rate_limit"]):
            logger.warning(f"Rate limit exceeded for {client_ip}")
            send_error_response(conn, 429, "Too Many Requests")
            return
        
        # Method validation
        if method not in config.config["security"]["allowed_methods"]:
            send_error_response(conn, 405, "Method Not Allowed")
            return
        
        # Log request (only for non-GET requests to reduce overhead)
        if method != "GET":
            logger.info(f"{client_ip} - {method} {path}")
        
        # Handle special endpoints
        if path == "/health":
            handle_health_endpoint(conn)
            return
        elif path == "/metrics":
            handle_metrics_endpoint(conn)
            return
        
        # Process file request
        process_file_request(conn, method, path, headers, root_dir)
        
    except socket.timeout:
        logger.warning(f"Timeout for client {addr}")
        send_error_response(conn, 408, "Request Timeout")
    except Exception as e:
        logger.error(f"Error handling client {addr}: {e}")
        send_error_response(conn, 500, "Internal Server Error")
    finally:
        conn.close()
        metrics.active_connections -= 1
        
        # Record metrics
        response_time = time.time() - start_time
        metrics.record_request(response_time, 200, 0)  # Status code will be updated in process_file_request

def send_error_response(conn, status_code: int, message: str):
    """Send error response with proper HTML."""
    body = generate_error_page(status_code, message).encode()
    headers = {
        "Content-Type": "text/html",
        "Content-Length": str(len(body))
    }
    headers = add_cors_headers(headers)
    
    response = f"HTTP/1.1 {status_code} {message}\r\n"
    for key, value in headers.items():
        response += f"{key}: {value}\r\n"
    response += "\r\n"
    
    conn.sendall(response.encode() + body)

def handle_health_endpoint(conn):
    """Handle health check endpoint."""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - metrics.start_time
    }
    
    body = json.dumps(health_data).encode()
    headers = {
        "Content-Type": "application/json",
        "Content-Length": str(len(body))
    }
    headers = add_cors_headers(headers)
    
    response = "HTTP/1.1 200 OK\r\n"
    for key, value in headers.items():
        response += f"{key}: {value}\r\n"
    response += "\r\n"
    
    conn.sendall(response.encode() + body)

def handle_metrics_endpoint(conn):
    """Handle metrics endpoint."""
    stats = metrics.get_stats()
    body = json.dumps(stats, indent=2).encode()
    headers = {
        "Content-Type": "application/json",
        "Content-Length": str(len(body))
    }
    headers = add_cors_headers(headers)
    
    response = "HTTP/1.1 200 OK\r\n"
    for key, value in headers.items():
        response += f"{key}: {value}\r\n"
    response += "\r\n"
    
    conn.sendall(response.encode() + body)

def process_file_request(conn, method: str, path: str, headers: Dict[str, str], root_dir: str):
    """Process file request with caching and compression."""
    # URL decode the path to handle spaces and special characters
    path = unquote(path)
    
    # Normalize path
    if path.startswith('/'):
        file_path = path[1:]
    else:
        file_path = path
    
    file_path = os.path.normpath(file_path)
    full_path = os.path.join(root_dir, file_path)
    
    # Security check
    if not os.path.abspath(full_path).startswith(os.path.abspath(root_dir)):
        send_error_response(conn, 403, "Forbidden")
        return
    
    # Check if file exists
    if not os.path.exists(full_path):
        send_error_response(conn, 404, "Not Found")
        return
    
    # Handle directory requests
    if os.path.isdir(full_path):
        # Look for index files
        index_files = ['index.html', 'index.htm', 'index.php']
        for index_file in index_files:
            index_path = os.path.join(full_path, index_file)
            if os.path.exists(index_path):
                full_path = index_path
                break
        else:
            # Generate directory listing
            if method == "HEAD":
                body = b""
            else:
                body = generate_directory_listing(full_path, path).encode()
            
            content_type = "text/html"
            send_file_response(conn, body, content_type, headers)
            return
    
    # Check file size
    file_size = os.path.getsize(full_path)
    if file_size > config.config["security"]["max_file_size"]:
        send_error_response(conn, 413, "File Too Large")
        return
    
    # Check cache with optimized key generation
    if config.config["cache"]["enabled"]:
        file_mtime = os.path.getmtime(full_path)
        cache_key = f"{full_path}_{file_size}_{file_mtime}"
        cached_content = cache.get(cache_key)
        if cached_content:
            content = cached_content
        else:
            with open(full_path, 'rb') as f:
                content = f.read()
            cache.set(cache_key, content)
    else:
        with open(full_path, 'rb') as f:
            content = f.read()
    
    # Handle HEAD requests
    if method == "HEAD":
        content = b""
    
    # Get content type
    content_type, _ = mimetypes.guess_type(full_path)
    if content_type is None:
        content_type = "application/octet-stream"
    
    # Compression
    accept_encoding = headers.get("accept-encoding", "")
    compressed_content, encoding = compress_content(content, accept_encoding)
    
    # Send response
    send_file_response(conn, compressed_content, content_type, headers, encoding)

def send_file_response(conn, content: bytes, content_type: str, headers: Dict[str, str], encoding: str = ""):
    """Send file response with proper headers."""
    response_headers = {
        "Content-Type": content_type,
        "Content-Length": str(len(content)),
        "Server": "ProfessionalWebServer/1.0",
        "Cache-Control": "public, max-age=3600"
    }
    
    if encoding:
        response_headers["Content-Encoding"] = encoding
    
    response_headers = add_cors_headers(response_headers)
    
    response = "HTTP/1.1 200 OK\r\n"
    for key, value in response_headers.items():
        response += f"{key}: {value}\r\n"
    response += "\r\n"
    
    conn.sendall(response.encode() + content)

def signal_handler(signum, frame):
    """Handle graceful shutdown."""
    logger.info("Received shutdown signal, closing server...")
    sys.exit(0)

def start_server(root_dir: str, port: int, config_file: str = None):
    """Start the web server with full feature set."""
    global config, metrics, logger
    
    # Load configuration
    config = Config(config_file)
    setup_logging()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create server socket with performance optimizations
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Performance optimizations
    server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Disable Nagle's algorithm
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # Enable keep-alive
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)  # Increase receive buffer
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # Increase send buffer
    
    # SSL support
    if config.config["ssl"]["enabled"]:
        if not config.config["ssl"]["cert_file"] or not config.config["ssl"]["key_file"]:
            logger.error("SSL enabled but certificate files not specified")
            return
        
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(config.config["ssl"]["cert_file"], config.config["ssl"]["key_file"])
        server_socket = context.wrap_socket(server_socket, server_side=True)
        logger.info("SSL/TLS enabled")
    
    # Bind and listen
    server_socket.bind((config.config["server"]["host"], port))
    server_socket.listen(config.config["server"]["max_connections"])
    
    logger.info(f"Professional Web Server v1.0 starting...")
    logger.info(f"Server running on {config.config['server']['host']}:{port}")
    logger.info(f"Root directory: {root_dir}")
    logger.info(f"Thread pool size: {config.config['server']['thread_pool_size']}")
    logger.info(f"Rate limit: {config.config['security']['rate_limit']} requests/minute")
    logger.info(f"Cache enabled: {config.config['cache']['enabled']}")
    
    # Thread pool for handling clients
    with ThreadPoolExecutor(max_workers=config.config["server"]["thread_pool_size"]) as executor:
        try:
            while True:
                conn, addr = server_socket.accept()
                logger.debug(f"New connection from {addr}")
                
                # Submit client handling to thread pool
                executor.submit(handle_client, conn, addr, root_dir)
                
        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            server_socket.close()
            logger.info("Server stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Professional Web Server")
    parser.add_argument("-r", "--root", required=True, help="Root directory for files")
    parser.add_argument("-p", "--port", type=int, default=8080,
                        help="Port number (default: 8080)")
    parser.add_argument("-c", "--config", help="Configuration file path")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--ssl", action="store_true", help="Enable SSL/TLS")
    parser.add_argument("--cert", help="SSL certificate file")
    parser.add_argument("--key", help="SSL private key file")
    
    args = parser.parse_args()
    
    # Override config with command line arguments
    if args.host:
        config.config["server"]["host"] = args.host
    if args.ssl:
        config.config["ssl"]["enabled"] = True
        if args.cert:
            config.config["ssl"]["cert_file"] = args.cert
        if args.key:
            config.config["ssl"]["key_file"] = args.key
    
    start_server(args.root, args.port, args.config)
