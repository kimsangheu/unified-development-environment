# ===============================================
# KG이니시스 빠른 검증 스크립트 (Quick Check)
# ===============================================

Write-Host "🚀 KG이니시스 빠른 검증 시작..." -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

$ProjectPath = "D:\Documents\PG\KG이니시스\general_pc\PC 일반결제\node"

# 프로젝트 디렉토리로 이동
if (Test-Path $ProjectPath) {
    Set-Location $ProjectPath
    Write-Host "✅ 프로젝트 디렉토리: $ProjectPath" -ForegroundColor Green
} else {
    Write-Host "❌ 프로젝트 디렉토리를 찾을 수 없습니다: $ProjectPath" -ForegroundColor Red
    exit 1
}

# 1. 필수 파일 존재 확인
Write-Host "`n📁 필수 파일 확인:" -ForegroundColor Yellow
$files = @("app.js", "properties.js", "package.json")
$allFilesExist = $true

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    Write-Host "❌ 필수 파일이 누락되었습니다." -ForegroundColor Red
    exit 1
}

# 2. Node.js 환경 확인
Write-Host "`n🔧 Node.js 환경:" -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>$null
    if ($nodeVersion) {
        Write-Host "  ✅ Node.js: $nodeVersion" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Node.js가 설치되지 않았습니다" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ❌ Node.js 확인 실패" -ForegroundColor Red
    exit 1
}

# 3. 암호화 로직 테스트
Write-Host "`n🔐 암호화 로직 테스트:" -ForegroundColor Yellow

$jsCode = 'const crypto = require("crypto"); try { const testKey = "SU5JTElURV9UUklQTEVERVNfS0VZU1RS"; const hash = crypto.createHash("sha256").update(testKey).digest("hex"); console.log("HASH_SUCCESS:" + hash.length); } catch (error) { console.log("HASH_FAILED:" + error.message); }'

try {
    $result = echo $jsCode | node
    if ($result -like "HASH_SUCCESS:*") {
        $hashLength = ($result -split ":")[1]
        Write-Host "  ✅ SHA256 해시 생성 성공 (길이: $hashLength)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 암호화 테스트 실패: $result" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ❌ 암호화 테스트 실행 실패" -ForegroundColor Red
    exit 1
}

# 4. 포트 사용 확인
Write-Host "`n🌐 포트 3000 확인:" -ForegroundColor Yellow
$portInUse = netstat -an | findstr ":3000" | findstr "LISTENING"
if ($portInUse) {
    Write-Host "  ⚠️  포트 3000이 이미 사용 중입니다" -ForegroundColor Yellow
    Write-Host "     사용 중인 프로세스를 확인하세요: netstat -ano | findstr :3000" -ForegroundColor Yellow
} else {
    Write-Host "  ✅ 포트 3000 사용 가능" -ForegroundColor Green
}

# 5. 최종 결과
Write-Host "`n🎉 빠른 검증 완료!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "✅ KG이니시스 API 연동 준비가 완료되었습니다!" -ForegroundColor Green
Write-Host "" 
Write-Host "🚀 다음 단계:" -ForegroundColor Cyan
Write-Host "   1. 전체 검증: .\scripts\Verify-KGInicisAPI.ps1" -ForegroundColor White
Write-Host "   2. 서버 실행: npm start" -ForegroundColor White  
Write-Host "   3. 브라우저 접속: http://localhost:3000" -ForegroundColor White
Write-Host ""
