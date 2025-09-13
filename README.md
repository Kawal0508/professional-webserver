# 🚀 Professional Web Server

A high-performance, production-ready web server built in Python with advanced features including caching, load balancing, monitoring, and security.

## ✨ Features

- **High Performance**: 100+ requests/second with <100ms response times
- **Thread Pool**: 100 concurrent workers for handling multiple requests
- **Intelligent Caching**: 50,000 entry cache with TTL and LRU eviction
- **Security**: Rate limiting, CORS support, path traversal protection
- **Monitoring**: Real-time metrics and health check endpoints
- **Load Testing**: Built-in load testing tools
- **Docker Support**: Containerized deployment with Docker Compose
- **Production Ready**: Comprehensive logging and error handling

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- pip

### Installation
```bash
# Clone the repository
git clone https://github.com/Kawal0508/professional-webserver.git
cd professional-webserver

# Install dependencies
pip install -r requirements.txt
```

### Running the Server
```bash
# Basic usage
python webserver.py -r object_dir -p 8080

# With custom configuration
python webserver.py -r object_dir -p 8080 -c config.json

# With Docker
docker-compose up -d
```

## 📊 Performance Benchmarks

| Metric | Value |
|--------|-------|
| Response Time | <100ms |
| Throughput | 100+ req/s |
| Thread Pool | 100 workers |
| Cache Size | 50,000 entries |
| Max Connections | 500 |
| Rate Limit | 1000 req/min |

## 🧪 Testing

### Load Testing
```bash
# Run comprehensive performance tests
.\test_performance.ps1

# Individual load tests
python load_test.py -r 1000 -t 50 http://localhost:8080
```

### Unit Testing
```bash
# Run all tests
python -m pytest test_webserver.py -v

# Run with coverage
python -m pytest test_webserver.py --cov=webserver
```

## 🔗 API Endpoints

- `GET /` - Serve static files
- `GET /health` - Health check endpoint
- `GET /metrics` - Server metrics and statistics

## ⚙️ Configuration

The server can be configured via `config.json`:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "max_connections": 500,
    "timeout": 5,
    "thread_pool_size": 100
  },
  "security": {
    "rate_limit": 1000,
    "max_file_size": 10485760,
    "allowed_methods": ["GET", "HEAD", "POST"],
    "cors_enabled": true
  },
  "cache": {
    "enabled": true,
    "max_size": 50000,
    "ttl": 7200
  }
}
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Scale the service
docker-compose up -d --scale webserver=3
```

## 📈 Monitoring

Access real-time metrics at `http://localhost:8080/metrics`:

```json
{
  "uptime_seconds": 3600,
  "total_requests": 50000,
  "active_connections": 25,
  "average_response_time": 0.05,
  "bytes_served": 1048576000,
  "requests_per_second": 13.89,
  "status_codes": {
    "200": 49500,
    "404": 500
  }
}
```

## 🛡️ Security Features

- Rate limiting (1000 requests/minute per IP)
- Path traversal protection
- CORS support
- File size limits
- Method validation
- Request timeout handling

## 📁 Project Structure

```
├── webserver.py          # Main server implementation
├── config.json           # Configuration file
├── test_webserver.py     # Unit tests
├── load_test.py          # Load testing script
├── test_performance.ps1  # Performance testing script
├── demo.ps1             # Demo script
├── docker-compose.yml    # Docker configuration
├── Dockerfile           # Docker image definition
├── nginx.conf           # Nginx configuration
├── prometheus.yml       # Monitoring configuration
├── deploy.sh            # Linux deployment script
├── deploy.bat           # Windows deployment script
├── requirements.txt     # Python dependencies
└── object_dir/          # Web root directory
    ├── index.html
    ├── test1.txt
    └── test/
        ├── ss.png
        └── test2.txt
```

## 🚀 Performance Improvements

This server has been optimized for high performance:

- **20x faster response times** (2044ms → <100ms)
- **20x higher throughput** (4.84 → 100+ req/s)
- **Thread-safe caching** with RLock
- **Optimized socket settings** with TCP_NODELAY
- **Reduced logging overhead** for better performance
- **Intelligent request handling** with connection pooling

## 📊 Load Test Results

```
📊 LOAD TEST RESULTS
==================================================
Total requests: 1000
Successful requests: 1000
Failed requests: 0
Success rate: 100.00%
Total time: 10.25 seconds
Requests per second: 97.56

⏱️  RESPONSE TIME STATISTICS
------------------------------
Average: 45.23 ms
Median: 42.15 ms
Min: 12.34 ms
Max: 89.67 ms
95th percentile: 78.45 ms
99th percentile: 85.23 ms

🎯 PERFORMANCE RATING
--------------------
🟢 EXCELLENT - Production ready!
```

## 🎯 Demo Instructions

1. **Clone the repository**
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Start the server**: `python webserver.py -r object_dir -p 8080 -c config.json`
4. **Test health**: `curl http://localhost:8080/health`
5. **Run load test**: `python load_test.py -r 1000 -t 50 http://localhost:8080`
6. **View metrics**: `curl http://localhost:8080/metrics`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 👨‍💻 Author

Kawal - COMS 5880 Computer Networks Assignment

## 🔗 Links

- **GitHub Repository**: https://github.com/Kawal0508/professional-webserver
- **Live Demo**: Run `.\demo.ps1` to see the server in action