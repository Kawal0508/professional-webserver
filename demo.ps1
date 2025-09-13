Write-Host "�� Professional Web Server Demo" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green
Write-Host "Repository: https://github.com/Kawal0508/professional-webserver" -ForegroundColor Cyan

Write-Host "`n1. Starting optimized web server..." -ForegroundColor Yellow
Start-Process python -ArgumentList "webserver.py", "-r", "object_dir", "-p", "8080", "-c", "config.json" -WindowStyle Minimized

Write-Host "   Waiting for server to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

Write-Host "`n2. Testing health endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing
    Write-Host "   ✅ Health check passed: $($health.StatusCode)" -ForegroundColor Green
    $healthData = $health.Content | ConvertFrom-Json
    Write-Host "   Server uptime: $([math]::Round($healthData.uptime, 2)) seconds" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Health check failed" -ForegroundColor Red
}

Write-Host "`n3. Running performance test..." -ForegroundColor Yellow
python load_test.py -r 500 -t 25 http://localhost:8080

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
Get-Process python | Where-Object {$_.MainWindowTitle -like "*webserver*"} | Stop-Process
Write-Host "`nServer stopped." -ForegroundColor Yellow