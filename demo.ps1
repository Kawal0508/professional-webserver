Write-Host "🚀 Professional Web Server Demo" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green
Write-Host "Repository: https://github.com/Kawal0508/professional-webserver" -ForegroundColor Cyan

Write-Host "`n1. Starting optimized web server..." -ForegroundColor Yellow
Write-Host "   Starting server in background..." -ForegroundColor Cyan

# Start server in background
$serverJob = Start-Job -ScriptBlock {
    Set-Location "E:\Iowa State University 2025 - 2027\Spring 2025\COMS 5880 - Computer Networks\Programming Assignment 2"
    python webserver.py -r object_dir -p 8080 -c config.json
}

Write-Host "   Waiting for server to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# Check if server is running
Write-Host "`n2. Checking if server is running..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing -TimeoutSec 10
    Write-Host "   ✅ Health check passed: $($health.StatusCode)" -ForegroundColor Green
    $healthData = $health.Content | ConvertFrom-Json
    Write-Host "   Server uptime: $([math]::Round($healthData.uptime, 2)) seconds" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Health check failed - Server not running" -ForegroundColor Red
    Write-Host "   Please start the server manually:" -ForegroundColor Yellow
    Write-Host "   python webserver.py -r object_dir -p 8080 -c config.json" -ForegroundColor Cyan
    exit 1
}

Write-Host "`n3. Running performance test..." -ForegroundColor Yellow
python load_test.py -r 100 -t 10 http://localhost:8080

Write-Host "`n4. Getting server metrics..." -ForegroundColor Yellow
try {
    $metrics = Invoke-WebRequest -Uri "http://localhost:8080/metrics" -UseBasicParsing
    $metricsData = $metrics.Content | ConvertFrom-Json
    Write-Host "   Total requests: $($metricsData.total_requests)" -ForegroundColor Green
    Write-Host "   Requests/second: $([math]::Round($metricsData.requests_per_second, 2))" -ForegroundColor Green
    Write-Host "   Average response time: $([math]::Round($metricsData.average_response_time * 1000, 2)) ms" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Could not retrieve metrics" -ForegroundColor Red
}

Write-Host "`n5. Testing file serving..." -ForegroundColor Yellow
try {
    $file = Invoke-WebRequest -Uri "http://localhost:8080/test1.txt" -UseBasicParsing
    Write-Host "   ✅ File serving works: $($file.StatusCode)" -ForegroundColor Green
    Write-Host "   Content preview: $($file.Content.Substring(0, [Math]::Min(50, $file.Content.Length)))..." -ForegroundColor Green
} catch {
    Write-Host "   ❌ File serving failed" -ForegroundColor Red
}

Write-Host "`n✅ Demo completed! Server is running on http://localhost:8080" -ForegroundColor Green
Write-Host "GitHub Repository: https://github.com/Kawal0508/professional-webserver" -ForegroundColor Cyan
Write-Host "Press any key to stop the server..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Stop the server
Stop-Job $serverJob
Remove-Job $serverJob
Write-Host "`nServer stopped." -ForegroundColor Yellow