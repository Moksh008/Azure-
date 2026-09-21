param(
    [string]$ApiBaseUrl = "https://api-r2b-moksh.azurewebsites.net",
    [string]$FrontendUrl = "https://icy-pond-06feb7300.4.azurestaticapps.net"
)

Write-Host "========================================================="
Write-Host "  Research2Build -- Live Azure Verification Suite        "
Write-Host "========================================================="

# Test 1: Frontend SWA
Write-Host "`n[1/4] Checking Frontend Static Web App: $FrontendUrl..."
try {
    $fe = Invoke-WebRequest -Uri $FrontendUrl -Method GET -TimeoutSec 15
    if ($fe.StatusCode -eq 200) {
        Write-Host " [PASS] Frontend returned HTTP 200 OK"
    } else {
        Write-Host " [WARN] Frontend returned HTTP $($fe.StatusCode)"
    }
} catch {
    Write-Host " [FAIL] Frontend request failed"
}

# Test 2: Backend Health
Write-Host "`n[2/4] Checking Backend API Health: $ApiBaseUrl/health..."
try {
    $health = Invoke-RestMethod -Uri "$ApiBaseUrl/health" -Method GET -TimeoutSec 20
    Write-Host " [PASS] Health Response:"
    Write-Host ($health | ConvertTo-Json -Compress)
} catch {
    Write-Host " [FAIL] Health check failed"
}

# Test 3: Backend Swagger Docs
Write-Host "`n[3/4] Checking OpenAPI Docs: $ApiBaseUrl/docs..."
try {
    $docs = Invoke-WebRequest -Uri "$ApiBaseUrl/docs" -Method GET -TimeoutSec 15
    if ($docs.StatusCode -eq 200) {
        Write-Host " [PASS] OpenAPI Docs returned HTTP 200 OK"
    }
} catch {
    Write-Host " [FAIL] OpenAPI Docs request failed"
}

# Test 4: OpenAlex Topic Discovery Endpoint
Write-Host "`n[4/4] Testing Topic Discovery Endpoint: $ApiBaseUrl/discovery/search..."
try {
    $discBody = '{"query":"quantum computing","max_results":3}'
    $disc = Invoke-RestMethod -Uri "$ApiBaseUrl/discovery/search" -Method POST -Body $discBody -ContentType "application/json" -TimeoutSec 25
    Write-Host " [PASS] Topic Discovery returned papers successfully"
} catch {
    Write-Host " [FAIL] Topic Discovery test failed"
}

Write-Host "`n========================================================="
Write-Host "  Verification Completed                                 "
Write-Host "========================================================="
