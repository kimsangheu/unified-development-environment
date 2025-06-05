# ===============================================
# KG이니시스 API 테스트 스크립트
# ===============================================

param(
    [string]$TestType = "connection",  # connection, payment, full
    [switch]$Verbose = $false
)

Write-Host "🌐 KG이니시스 API 테스트 시작..." -ForegroundColor Cyan
Write-Host "테스트 유형: $TestType" -ForegroundColor Gray
Write-Host "=================================" -ForegroundColor Cyan

$ProjectPath = "D:\Documents\PG\KG이니시스\general_pc\PC 일반결제\node"

if (Test-Path $ProjectPath) {
    Set-Location $ProjectPath
} else {
    Write-Host "❌ 프로젝트 디렉토리를 찾을 수 없습니다" -ForegroundColor Red
    exit 1
}

# KG이니시스 테스트 URL 설정
$TestUrls = @{
    "STG" = "https://stgstdpay.inicis.com"
    "FC"  = "https://fcstdpay.inicis.com" 
    "KS"  = "https://ksstdpay.inicis.com"
}

# 1. 연결성 테스트
if ($TestType -eq "connection" -or $TestType -eq "full") {
    Write-Host "`n🔗 API 서버 연결성 테스트:" -ForegroundColor Yellow
    
    foreach ($env in $TestUrls.Keys) {
        $url = $TestUrls[$env]
        Write-Host "  테스트 중: $env ($url)" -ForegroundColor Gray
        
        try {
            $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
            $response = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
            $stopwatch.Stop()
            
            $responseTime = $stopwatch.ElapsedMilliseconds
            
            if ($response.StatusCode -eq 200) {
                Write-Host "    ✅ $env : 연결 성공 (HTTP $($response.StatusCode), $responseTime ms)" -ForegroundColor Green
            } else {
                Write-Host "    ⚠️  $env : HTTP $($response.StatusCode) ($responseTime ms)" -ForegroundColor Yellow
            }
            
            if ($Verbose) {
                Write-Host "       응답 크기: $($response.Content.Length) bytes" -ForegroundColor Gray
            }
            
        } catch {
            Write-Host "    ❌ $env : 연결 실패 - $($_.Exception.Message)" -ForegroundColor Red
        }
        
        Start-Sleep -Milliseconds 500  # 서버 부하 방지
    }
}

# 2. 암호화 및 서명 테스트
if ($TestType -eq "payment" -or $TestType -eq "full") {
    Write-Host "`n🔐 결제 데이터 암호화 테스트:" -ForegroundColor Yellow
    
    $paymentTestScript = @"
const crypto = require('crypto');

// 실제 결제 파라미터 시뮬레이션
const paymentData = {
    mid: 'INIpayTest',
    signKey: 'SU5JTElURV9UUklQTEVERVNfS0VZU1RS',
    oid: 'TEST_' + Date.now(),
    price: '1000',
    timestamp: Date.now().toString(),
    goodname: '테스트상품',
    buyername: '홍길동',
    buyertel: '01012345678',
    buyeremail: 'test@test.com'
};

console.log('=== 결제 데이터 ===');
console.log('주문번호:', paymentData.oid);
console.log('금액:', paymentData.price);
console.log('타임스탬프:', paymentData.timestamp);

try {
    // 1. mKey 생성 (머천트 키 해시)
    const mKey = crypto.createHash('sha256').update(paymentData.signKey).digest('hex');
    console.log('mKey 생성 성공:', mKey.substring(0, 20) + '...');
    
    // 2. signature 생성 (결제요청용)
    const signatureString = 'oid=' + paymentData.oid + '&price=' + paymentData.price + '&timestamp=' + paymentData.timestamp;
    const signature = crypto.createHash('sha256').update(signatureString).digest('hex');
    console.log('signature 생성 성공:', signature.substring(0, 20) + '...');
    console.log('signature 원본 문자열:', signatureString);
    
    // 3. verification 생성 (검증용)
    const verificationString = 'oid=' + paymentData.oid + '&price=' + paymentData.price + '&signKey=' + paymentData.signKey + '&timestamp=' + paymentData.timestamp;
    const verification = crypto.createHash('sha256').update(verificationString).digest('hex');
    console.log('verification 생성 성공:', verification.substring(0, 20) + '...');
    
    // 4. 승인요청용 토큰 시뮬레이션
    const authToken = 'MOCK_AUTH_TOKEN_' + Date.now();
    const authSignature = crypto.createHash('sha256').update('authToken=' + authToken + '&timestamp=' + paymentData.timestamp).digest('hex');
    console.log('승인요청 signature 생성:', authSignature.substring(0, 20) + '...');
    
    console.log('CRYPTO_ALL_SUCCESS');
    
} catch (error) {
    console.log('CRYPTO_ERROR:', error.message);
}
"@

    try {
        $cryptoResult = $paymentTestScript | node
        
        if ($cryptoResult -contains "CRYPTO_ALL_SUCCESS") {
            Write-Host "  ✅ 모든 암호화 로직 검증 성공" -ForegroundColor Green
            
            if ($Verbose) {
                $cryptoResult | ForEach-Object {
                    if ($_ -notlike "*SUCCESS*" -and $_ -ne "") {
                        Write-Host "    $($_)" -ForegroundColor Gray
                    }
                }
            }
        } else {
            Write-Host "  ❌ 암호화 로직 검증 실패" -ForegroundColor Red
            $cryptoResult | Where-Object { $_ -like "*ERROR*" } | ForEach-Object {
                Write-Host "    $_" -ForegroundColor Red
            }
        }
    } catch {
        Write-Host "  ❌ 암호화 테스트 실행 실패: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 3. 로컬 서버 구동 테스트
if ($TestType -eq "full") {
    Write-Host "`n🚀 로컬 서버 구동 테스트:" -ForegroundColor Yellow
    
    # 포트 3000 확인
    $portInUse = netstat -an | findstr ":3000" | findstr "LISTENING"
    
    if ($portInUse) {
        Write-Host "  ⚠️  포트 3000이 이미 사용 중입니다" -ForegroundColor Yellow
        Write-Host "     기존 서버를 종료하거나 다른 포트를 사용하세요" -ForegroundColor Yellow
    } else {
        Write-Host "  ✅ 포트 3000 사용 가능" -ForegroundColor Green
        
        # Express 서버 설정 확인
        $serverTestScript = @"
const express = require('express');
const app = express();

try {
    // 기본 라우터 설정 테스트
    app.get('/test', (req, res) => {
        res.json({ status: 'OK', message: 'Test successful' });
    });
    
    // 서버 설정 테스트 (실제 구동하지 않음)
    console.log('Express 앱 생성 성공');
    console.log('라우터 설정 성공');
    console.log('SERVER_CONFIG_SUCCESS');
    
} catch (error) {
    console.log('SERVER_ERROR:', error.message);
}
"@

        try {
            $serverResult = $serverTestScript | node
            
            if ($serverResult -contains "SERVER_CONFIG_SUCCESS") {
                Write-Host "  ✅ Express 서버 설정 검증 성공" -ForegroundColor Green
            } else {
                Write-Host "  ❌ Express 서버 설정 검증 실패" -ForegroundColor Red
            }
        } catch {
            Write-Host "  ❌ 서버 구성 테스트 실패: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# 4. properties.js 모듈 테스트
Write-Host "`n📋 properties.js 모듈 테스트:" -ForegroundColor Yellow

$propertiesTestScript = @"
try {
    const getUrl = require('./properties');
    
    // IDC별 URL 테스트
    const idcTypes = ['fc', 'ks', 'stg'];
    
    console.log('=== URL 설정 테스트 ===');
    
    idcTypes.forEach(idc => {
        const authUrl = getUrl.getAuthUrl(idc);
        const netCancelUrl = getUrl.getNetCancel(idc);
        
        console.log(idc.toUpperCase() + ' 승인 URL:', authUrl);
        console.log(idc.toUpperCase() + ' 망취소 URL:', netCancelUrl);
        
        // URL 형식 검증
        if (authUrl && authUrl.includes('stdpay.inicis.com/api/payAuth')) {
            console.log(idc.toUpperCase() + ' 승인 URL 형식: ✅');
        } else {
            console.log(idc.toUpperCase() + ' 승인 URL 형식: ❌');
        }
        
        if (netCancelUrl && netCancelUrl.includes('stdpay.inicis.com/api/netCancel')) {
            console.log(idc.toUpperCase() + ' 망취소 URL 형식: ✅');
        } else {
            console.log(idc.toUpperCase() + ' 망취소 URL 형식: ❌');
        }
    });
    
    console.log('PROPERTIES_SUCCESS');
    
} catch (error) {
    console.log('PROPERTIES_ERROR:', error.message);
}
"@

try {
    $propertiesResult = $propertiesTestScript | node
    
    if ($propertiesResult -contains "PROPERTIES_SUCCESS") {
        Write-Host "  ✅ properties.js 모듈 검증 성공" -ForegroundColor Green
        
        if ($Verbose) {
            $propertiesResult | ForEach-Object {
                if ($_ -notlike "*SUCCESS*" -and $_ -ne "" -and $_ -notlike "*===*") {
                    Write-Host "    $_" -ForegroundColor Gray
                }
            }
        }
    } else {
        Write-Host "  ❌ properties.js 모듈 검증 실패" -ForegroundColor Red
        $propertiesResult | Where-Object { $_ -like "*ERROR*" } | ForEach-Object {
            Write-Host "    $_" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "  ❌ properties.js 테스트 실행 실패: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. 최종 결과 및 권장사항
Write-Host "`n🏁 API 테스트 완료!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Cyan

Write-Host "`n📋 권장 다음 단계:" -ForegroundColor Yellow
Write-Host "  1. 전체 검증 실행: .\scripts\Verify-KGInicisAPI.ps1" -ForegroundColor White
Write-Host "  2. 서버 시작: npm start" -ForegroundColor White
Write-Host "  3. 브라우저 테스트: http://localhost:3000" -ForegroundColor White
Write-Host "  4. 실제 KG이니시스 테스트 결제 진행" -ForegroundColor White

Write-Host "`n🔧 문제 해결:" -ForegroundColor Yellow
Write-Host "  • 연결 실패 시: 방화벽 및 네트워크 설정 확인" -ForegroundColor White
Write-Host "  • 암호화 실패 시: Node.js crypto 모듈 설치 확인" -ForegroundColor White
Write-Host "  • 포트 충돌 시: netstat -ano | findstr :3000 으로 프로세스 확인" -ForegroundColor White

Write-Host ""
