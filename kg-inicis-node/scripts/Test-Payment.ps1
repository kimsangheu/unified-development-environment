# ===============================================
# KG이니시스 실제 결제 테스트 스크립트
# ===============================================

param(
    [string]$Amount = "1000",
    [string]$OrderId = "",
    [switch]$AutoBrowser = $false
)

Write-Host "💳 KG이니시스 실제 결제 테스트" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

$ProjectPath = "D:\Documents\PG\KG이니시스\general_pc\PC 일반결제\node"

if (Test-Path $ProjectPath) {
    Set-Location $ProjectPath
} else {
    Write-Host "❌ 프로젝트 디렉토리를 찾을 수 없습니다" -ForegroundColor Red
    exit 1
}

# 주문번호 생성 (미제공시)
if (-not $OrderId) {
    $OrderId = "TEST_" + (Get-Date -Format "yyyyMMddHHmmss")
}

Write-Host "결제 정보:" -ForegroundColor Yellow
Write-Host "  주문번호: $OrderId" -ForegroundColor White
Write-Host "  결제금액: $Amount 원" -ForegroundColor White
Write-Host "  테스트 상점: INIpayTest" -ForegroundColor White

# 1. 서버 실행 상태 확인
Write-Host "`n🔍 서버 상태 확인:" -ForegroundColor Yellow

$portInUse = netstat -an | findstr ":3000" | findstr "LISTENING"

if ($portInUse) {
    Write-Host "  ✅ 서버가 포트 3000에서 실행 중입니다" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  서버가 실행되지 않았습니다" -ForegroundColor Yellow
    Write-Host "     서버를 시작하시겠습니까? (Y/N): " -NoNewline -ForegroundColor Yellow
    
    $response = Read-Host
    if ($response -eq "Y" -or $response -eq "y") {
        Write-Host "  🚀 서버 시작 중..." -ForegroundColor Cyan
        
        # 백그라운드에서 서버 시작
        Start-Process -FilePath "cmd" -ArgumentList "/c", "cd `"$ProjectPath`" && npm start" -WindowStyle Minimized
        
        # 서버가 시작될 때까지 잠시 대기
        Write-Host "     서버 시작을 위해 5초 대기..." -ForegroundColor Gray
        Start-Sleep -Seconds 5
        
        # 다시 확인
        $portInUse = netstat -an | findstr ":3000" | findstr "LISTENING"
        if ($portInUse) {
            Write-Host "  ✅ 서버 시작 완료!" -ForegroundColor Green
        } else {
            Write-Host "  ❌ 서버 시작 실패. 수동으로 'npm start'를 실행해주세요" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "  ℹ️  수동으로 서버를 시작한 후 다시 실행해주세요: npm start" -ForegroundColor Cyan
        exit 1
    }
}

# 2. 로컬 서버 응답 테스트
Write-Host "`n🌐 로컬 서버 응답 테스트:" -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
    
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✅ 서버 응답 정상 (HTTP $($response.StatusCode))" -ForegroundColor Green
        Write-Host "     응답 크기: $($response.Content.Length) bytes" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠️  서버 응답: HTTP $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ 서버 응답 실패: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "     서버가 정상적으로 실행되고 있는지 확인해주세요" -ForegroundColor Yellow
    exit 1
}

# 3. 결제 데이터 생성 및 검증
Write-Host "`n🔐 결제 데이터 생성:" -ForegroundColor Yellow

$paymentDataScript = @"
const crypto = require('crypto');

const paymentData = {
    mid: 'INIpayTest',
    signKey: 'SU5JTElURV9UUklQTEVERVNfS0VZU1RS',
    oid: '$OrderId',
    price: '$Amount',
    timestamp: Date.now().toString(),
    goodname: '테스트상품',
    buyername: '홍길동',
    buyertel: '01012345678',
    buyeremail: 'test@test.com'
};

try {
    // 필수 해시 생성
    const mKey = crypto.createHash('sha256').update(paymentData.signKey).digest('hex');
    const signature = crypto.createHash('sha256').update('oid=' + paymentData.oid + '&price=' + paymentData.price + '&timestamp=' + paymentData.timestamp).digest('hex');
    const verification = crypto.createHash('sha256').update('oid=' + paymentData.oid + '&price=' + paymentData.price + '&signKey=' + paymentData.signKey + '&timestamp=' + paymentData.timestamp).digest('hex');
    
    console.log('=== 생성된 결제 데이터 ===');
    console.log('주문번호: ' + paymentData.oid);
    console.log('결제금액: ' + paymentData.price + '원');
    console.log('타임스탬프: ' + paymentData.timestamp);
    console.log('mKey: ' + mKey.substring(0, 20) + '...');
    console.log('signature: ' + signature.substring(0, 20) + '...');
    console.log('verification: ' + verification.substring(0, 20) + '...');
    console.log('PAYMENT_DATA_SUCCESS');
    
} catch (error) {
    console.log('PAYMENT_DATA_ERROR: ' + error.message);
}
"@

try {
    $paymentResult = $paymentDataScript | node
    
    if ($paymentResult -contains "PAYMENT_DATA_SUCCESS") {
        Write-Host "  ✅ 결제 데이터 생성 성공" -ForegroundColor Green
        
        # 결제 데이터 상세 출력
        $paymentResult | ForEach-Object {
            if ($_ -like "주문번호:*" -or $_ -like "결제금액:*" -or $_ -like "타임스탬프:*") {
                Write-Host "    $_" -ForegroundColor White
            } elseif ($_ -like "*Key:*" -or $_ -like "*signature:*" -or $_ -like "*verification:*") {
                Write-Host "    $_" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "  ❌ 결제 데이터 생성 실패" -ForegroundColor Red
        $paymentResult | Where-Object { $_ -like "*ERROR*" } | ForEach-Object {
            Write-Host "    $_" -ForegroundColor Red
        }
        exit 1
    }
} catch {
    Write-Host "  ❌ 결제 데이터 생성 테스트 실패: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 4. 브라우저 테스트 안내
Write-Host "`n🌍 브라우저 테스트:" -ForegroundColor Yellow

$testUrl = "http://localhost:3000"

if ($AutoBrowser) {
    Write-Host "  🚀 브라우저를 자동으로 열고 있습니다..." -ForegroundColor Cyan
    Start-Process $testUrl
    Start-Sleep -Seconds 2
} else {
    Write-Host "  📋 수동 테스트 절차:" -ForegroundColor White
    Write-Host "     1. 브라우저에서 다음 URL을 열어주세요:" -ForegroundColor White
    Write-Host "        $testUrl" -ForegroundColor Cyan
    Write-Host "     2. 결제 정보를 확인하고 '결제 요청' 버튼을 클릭하세요" -ForegroundColor White
    Write-Host "     3. KG이니시스 결제창에서 테스트 결제를 진행하세요" -ForegroundColor White
    Write-Host ""
    Write-Host "  브라우저를 자동으로 여시겠습니까? (Y/N): " -NoNewline -ForegroundColor Yellow
    
    $browserResponse = Read-Host
    if ($browserResponse -eq "Y" -or $browserResponse -eq "y") {
        Write-Host "  🚀 브라우저 열기..." -ForegroundColor Cyan
        Start-Process $testUrl
    }
}

# 5. 테스트 체크리스트
Write-Host "`n📋 결제 테스트 체크리스트:" -ForegroundColor Yellow
Write-Host "  □ 결제 요청 페이지가 정상적으로 로드되는가?" -ForegroundColor White
Write-Host "  □ 주문번호, 금액, 상품명이 올바르게 표시되는가?" -ForegroundColor White
Write-Host "  □ '결제 요청' 버튼 클릭 시 KG이니시스 창이 열리는가?" -ForegroundColor White
Write-Host "  □ 테스트 결제가 정상적으로 진행되는가?" -ForegroundColor White
Write-Host "  □ 결제 완료 후 결과 페이지가 정상적으로 표시되는가?" -ForegroundColor White

# 6. 테스트 카드 정보 안내
Write-Host "`n💳 KG이니시스 테스트 카드 정보:" -ForegroundColor Yellow
Write-Host "  테스트용 카드번호들 (실제 결제되지 않음):" -ForegroundColor Gray
Write-Host "  • 신용카드: 4000-0000-0000-0001" -ForegroundColor White
Write-Host "  • 체크카드: 4000-0000-0000-0002" -ForegroundColor White
Write-Host "  • 유효기간: 아무 미래 날짜 (예: 12/25)" -ForegroundColor White
Write-Host "  • CVC: 아무 3자리 숫자 (예: 123)" -ForegroundColor White
Write-Host "  • 비밀번호: 아무 숫자 (예: 1234)" -ForegroundColor White

# 7. 로그 모니터링 안내
Write-Host "`n📊 실시간 로그 모니터링:" -ForegroundColor Yellow
Write-Host "  서버 로그를 실시간으로 확인하려면:" -ForegroundColor White
Write-Host "  새 PowerShell 창에서 다음 명령어를 실행하세요:" -ForegroundColor White
Write-Host "  cd `"$ProjectPath`" && npm start" -ForegroundColor Cyan

Write-Host "`n🎉 결제 테스트 준비 완료!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "위의 체크리스트를 따라 테스트를 진행해주세요." -ForegroundColor White
Write-Host ""
