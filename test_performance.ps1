# Performance Testing Script for Web Server
# This script tests the server with different load patterns

Write-Host "🚀 Web Server Performance Testing" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Check if server is running
Write-Host "`n1. Checking if server is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "   ✅ Server is running (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Server is not running. Please start the server first:" -ForegroundColor Red
    Write-Host "   python webserver.py -r object_dir -p 8080 -c config.json" -ForegroundColor Cyan
    exit 1
}

# Test 1: Light load test
Write-Host "`n2. Light Load Test (100 requests, 10 threads)..." -ForegroundColor Yellow
Write-Host "   Running: python load_test.py -r 100 -t 10 http://localhost:8080" -ForegroundColor Cyan
python load_test.py -r 100 -t 10 http://localhost:8080

# Test 2: Medium load test
Write-Host "`n3. Medium Load Test (500 requests, 25 threads)..." -ForegroundColor Yellow
Write-Host "   Running: python load_test.py -r 500 -t 25 http://localhost:8080" -ForegroundColor Cyan
python load_test.py -r 500 -t 25 http://localhost:8080

# Test 3: Heavy load test
Write-Host "`n4. Heavy Load Test (1000 requests, 50 threads)..." -ForegroundColor Yellow
Write-Host "   Running: python load_test.py -r 1000 -t 50 http://localhost:8080" -ForegroundColor Cyan
python load_test.py -r 1000 -t 50 http://localhost:8080

# Test 4: Stress test
Write-Host "`n5. Stress Test (2000 requests, 100 threads)..." -ForegroundColor Yellow
Write-Host "   Running: python load_test.py -r 2000 -t 100 http://localhost:8080" -ForegroundColor Cyan
python load_test.py -r 2000 -t 100 http://localhost:8080

# Get final metrics
Write-Host "`n6. Final Server Metrics..." -ForegroundColor Yellow
try {
    $metrics = Invoke-WebRequest -Uri "http://localhost:8080/metrics" -UseBasicParsing
    $metricsData = $metrics.Content | ConvertFrom-Json
    Write-Host "   Total Requests: $($metricsData.total_requests)" -ForegroundColor Green
    Write-Host "   Uptime: $([math]::Round($metricsData.uptime_seconds, 2)) seconds" -ForegroundColor Green
    Write-Host "   Requests/Second: $([math]::Round($metricsData.requests_per_second, 2))" -ForegroundColor Green
    Write-Host "   Average Response Time: $([math]::Round($metricsData.average_response_time * 1000, 2)) ms" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Could not retrieve metrics" -ForegroundColor Red
}

Write-Host "`n✅ Performance testing completed!" -ForegroundColor Green
Write-Host "Check the results above to see if performance has improved." -ForegroundColor Cyan
