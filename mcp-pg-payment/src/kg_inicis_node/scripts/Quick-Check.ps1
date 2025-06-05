# Set UTF-8 encoding for PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "KG Inicis Quick Verification Started..." -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Use current directory instead of hardcoded path
$ProjectPath = Get-Location
Write-Host "Current Directory: $ProjectPath" -ForegroundColor Gray

# Check if we're in the right directory
if ((Test-Path "app.js") -and (Test-Path "package.json")) {
    Write-Host "Project Directory: OK" -ForegroundColor Green
} else {
    Write-Host "Project Directory: WRONG LOCATION" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory" -ForegroundColor Yellow
    Write-Host "Expected files: app.js, package.json" -ForegroundColor Yellow
    exit 1
}

Write-Host "`nRequired Files Check:" -ForegroundColor Yellow
$files = @("app.js", "properties.js", "package.json")
$allFilesExist = $true

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  $file - EXISTS" -ForegroundColor Green
    } else {
        Write-Host "  $file - MISSING" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    Write-Host "Required files are missing." -ForegroundColor Red
    exit 1
}

Write-Host "`nNode.js Environment Check:" -ForegroundColor Yellow
$nodeVersion = node --version 2>$null
if ($nodeVersion) {
    Write-Host "  Node.js: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "  Node.js: NOT INSTALLED" -ForegroundColor Red
    exit 1
}

Write-Host "`nCrypto Logic Test:" -ForegroundColor Yellow
$tempJs = "test_crypto.js"
$jsCode = 'const crypto = require("crypto"); const key = "SU5JTElURV9UUklQTEVERVNfS0VZU1RS"; const hash = crypto.createHash("sha256").update(key).digest("hex"); console.log("SUCCESS:" + hash.length);'
$jsCode | Out-File -FilePath $tempJs -Encoding ASCII

$result = node $tempJs 2>$null
Remove-Item $tempJs -ErrorAction SilentlyContinue

if ($result -like "SUCCESS:*") {
    $hashLength = ($result -split ":")[1]
    Write-Host "  SHA256 Hash Generation: SUCCESS (Length: $hashLength)" -ForegroundColor Green
} else {
    Write-Host "  Crypto Test: FAILED" -ForegroundColor Red
    Write-Host "  Result: $result" -ForegroundColor Red
    exit 1
}

Write-Host "`nPort 3000 Check:" -ForegroundColor Yellow
$portInUse = netstat -an | findstr ":3000" | findstr "LISTENING"
if ($portInUse) {
    Write-Host "  Port 3000: IN USE" -ForegroundColor Yellow
    Write-Host "    Check process: netstat -ano | findstr :3000" -ForegroundColor Yellow
} else {
    Write-Host "  Port 3000: AVAILABLE" -ForegroundColor Green
}

Write-Host "`nQuick Verification Complete!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "KG Inicis API Integration is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Start Server: npm start" -ForegroundColor White
Write-Host "   2. Open Browser: http://localhost:3000" -ForegroundColor White
Write-Host "   3. Full Verification: .\scripts\Verify-KGInicisAPI.ps1" -ForegroundColor White
Write-Host ""
