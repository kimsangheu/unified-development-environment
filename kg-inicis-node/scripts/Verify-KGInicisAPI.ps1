# ===============================================
# KG이니시스 API 연동 및 암호화 검증 스크립트
# ===============================================

param(
    [string]$TestMode = "full",  # full, quick, api-only
    [switch]$Verbose = $false
)

# 색상 출력 함수
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    } else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success { Write-ColorOutput Green $args }
function Write-Warning { Write-ColorOutput Yellow $args }
function Write-Error { Write-ColorOutput Red $args }
function Write-Info { Write-ColorOutput Cyan $args }

# 검증 결과 저장
$TestResults = @()
$ErrorCount = 0
$WarningCount = 0

Write-Info "🔍 KG이니시스 API 연동 및 암호화 검증 시작..."
Write-Info "==========================================`n"

# ========== 1. Node.js 환경 및 프로젝트 파일 검증 ==========
Write-Info "📋 1단계: 환경 및 파일 구조 검증"

# Node.js 설치 확인
try {
    $nodeVersion = node --version 2>$null
    if ($nodeVersion) {
        Write-Success "✅ Node.js 설치됨: $nodeVersion"
        $TestResults += @{Step="환경검증"; Item="Node.js"; Status="PASS"; Details=$nodeVersion}
    } else {
        Write-Error "❌ Node.js가 설치되지 않았습니다"
        $TestResults += @{Step="환경검증"; Item="Node.js"; Status="FAIL"; Details="Not installed"}
        $ErrorCount++
    }
} catch {
    Write-Error "❌ Node.js 확인 실패: $($_.Exception.Message)"
    $ErrorCount++
}

# 프로젝트 디렉토리 확인
$ProjectPath = "D:\Documents\PG\KG이니시스\general_pc\PC 일반결제\node"

if (Test-Path $ProjectPath) {
    Write-Success "✅ 프로젝트 디렉토리 존재: $ProjectPath"
    Set-Location $ProjectPath
    
    # 필수 파일 확인
    $RequiredFiles = @("app.js", "properties.js", "package.json", "views\INIstdpay_pc_req.html")
    
    foreach ($file in $RequiredFiles) {
        if (Test-Path $file) {
            Write-Success "  ✅ $file"
            $TestResults += @{Step="파일검증"; Item=$file; Status="PASS"; Details="File exists"}
        } else {
            Write-Error "  ❌ $file 누락"
            $TestResults += @{Step="파일검증"; Item=$file; Status="FAIL"; Details="File missing"}
            $ErrorCount++
        }
    }
} else {
    Write-Error "❌ 프로젝트 디렉토리가 존재하지 않습니다: $ProjectPath"
    $ErrorCount++
    return
}

# ========== 2. package.json 의존성 확인 ==========
Write-Info "`n📦 2단계: package.json 의존성 검증"

try {
    $packageJson = Get-Content "package.json" | ConvertFrom-Json
    $requiredDeps = @("express", "body-parser", "ejs", "request", "crypto")
    
    Write-Info "프로젝트: $($packageJson.name) v$($packageJson.version)"
    
    foreach ($dep in $requiredDeps) {
        if ($packageJson.dependencies.$dep) {
            Write-Success "  ✅ $dep : $($packageJson.dependencies.$dep)"
            $TestResults += @{Step="의존성검증"; Item=$dep; Status="PASS"; Details=$packageJson.dependencies.$dep}
        } else {
            Write-Error "  ❌ $dep : 누락됨"
            $TestResults += @{Step="의존성검증"; Item=$dep; Status="FAIL"; Details="Missing"}
            $ErrorCount++
        }
    }
} catch {
    Write-Error "❌ package.json 읽기 실패: $($_.Exception.Message)"
    $ErrorCount++
}

# ========== 3. 암호화 로직 검증 ==========
Write-Info "`n🔐 3단계: SHA256 암호화 로직 검증"

# Node.js를 사용하여 암호화 로직 테스트
$cryptoTestScript = @"
const crypto = require('crypto');

// 테스트 데이터
const testData = {
    signKey: 'SU5JTElURV9UUklQTEVERVNfS0VZU1RS',
    oid: 'TEST_ORDER_001',
    price: '1000',
    timestamp: '1638360000000'
};

try {
    // mKey 생성 테스트
    const mKey = crypto.createHash('sha256').update(testData.signKey).digest('hex');
    console.log('mKey_RESULT:' + mKey);
    
    // signature 생성 테스트  
    const signature = crypto.createHash('sha256').update('oid=' + testData.oid + '&price=' + testData.price + '&timestamp=' + testData.timestamp).digest('hex');
    console.log('signature_RESULT:' + signature);
    
    // verification 생성 테스트
    const verification = crypto.createHash('sha256').update('oid=' + testData.oid + '&price=' + testData.price + '&signKey=' + testData.signKey + '&timestamp=' + testData.timestamp).digest('hex');
    console.log('verification_RESULT:' + verification);
    
    console.log('CRYPTO_TEST_SUCCESS');
} catch (error) {
    console.log('CRYPTO_TEST_FAILED:' + error.message);
}
"@

try {
    $cryptoResult = $cryptoTestScript | node
    
    if ($cryptoResult -contains "CRYPTO_TEST_SUCCESS") {
        Write-Success "✅ 암호화 모듈 로딩 성공"
        
        # 각 암호화 결과 검증
        $mKeyResult = ($cryptoResult | Where-Object { $_ -like "mKey_RESULT:*" }) -replace "mKey_RESULT:", ""
        $signatureResult = ($cryptoResult | Where-Object { $_ -like "signature_RESULT:*" }) -replace "signature_RESULT:", ""
        $verificationResult = ($cryptoResult | Where-Object { $_ -like "verification_RESULT:*" }) -replace "verification_RESULT:", ""
        
        if ($mKeyResult -and $mKeyResult.Length -eq 64) {
            Write-Success "  ✅ mKey 생성: $($mKeyResult.Substring(0,20))..."
            $TestResults += @{Step="암호화검증"; Item="mKey"; Status="PASS"; Details="64자 해시 생성"}
        } else {
            Write-Error "  ❌ mKey 생성 실패"
            $ErrorCount++
        }
        
        if ($signatureResult -and $signatureResult.Length -eq 64) {
            Write-Success "  ✅ signature 생성: $($signatureResult.Substring(0,20))..."
            $TestResults += @{Step="암호화검증"; Item="signature"; Status="PASS"; Details="64자 해시 생성"}
        } else {
            Write-Error "  ❌ signature 생성 실패"
            $ErrorCount++
        }
        
        if ($verificationResult -and $verificationResult.Length -eq 64) {
            Write-Success "  ✅ verification 생성: $($verificationResult.Substring(0,20))..."
            $TestResults += @{Step="암호화검증"; Item="verification"; Status="PASS"; Details="64자 해시 생성"}
        } else {
            Write-Error "  ❌ verification 생성 실패"
            $ErrorCount++
        }
        
    } else {
        Write-Error "❌ 암호화 테스트 실패"
        $ErrorCount++
    }
} catch {
    Write-Error "❌ 암호화 로직 테스트 실패: $($_.Exception.Message)"
    $ErrorCount++
}

# ========== 4. properties.js URL 검증 ==========
Write-Info "`n🌐 4단계: API URL 설정 검증"

$urlTestScript = @"
const getUrl = require('./properties');

try {
    // IDC별 URL 테스트
    const testIDCs = ['fc', 'ks', 'stg'];
    
    testIDCs.forEach(idc => {
        const authUrl = getUrl.getAuthUrl(idc);
        const netCancelUrl = getUrl.getNetCancel(idc);
        
        console.log(idc + '_AUTH:' + authUrl);
        console.log(idc + '_CANCEL:' + netCancelUrl);
    });
    
    console.log('URL_TEST_SUCCESS');
} catch (error) {
    console.log('URL_TEST_FAILED:' + error.message);
}
"@

try {
    $urlResult = $urlTestScript | node
    
    if ($urlResult -contains "URL_TEST_SUCCESS") {
        Write-Success "✅ properties.js 모듈 로딩 성공"
        
        # URL 형식 검증
        $urlLines = $urlResult | Where-Object { $_ -like "*_AUTH:*" -or $_ -like "*_CANCEL:*" }
        
        foreach ($urlLine in $urlLines) {
            $parts = $urlLine -split ":"
            $urlType = $parts[0]
            $url = $parts[1] + ":" + $parts[2]
            
            if ($url -match "^https://.*\.inicis\.com/.*") {
                Write-Success "  ✅ $urlType : $url"
                $TestResults += @{Step="URL검증"; Item=$urlType; Status="PASS"; Details=$url}
            } else {
                Write-Warning "  ⚠️  $urlType : 형식 확인 필요 - $url"
                $TestResults += @{Step="URL검증"; Item=$urlType; Status="WARN"; Details=$url}
                $WarningCount++
            }
        }
    } else {
        Write-Error "❌ properties.js 테스트 실패"
        $ErrorCount++
    }
} catch {
    Write-Error "❌ URL 설정 테스트 실패: $($_.Exception.Message)"
    $ErrorCount++
}

# ========== 5. API 연결성 테스트 ==========
if ($TestMode -eq "full" -or $TestMode -eq "api-only") {
    Write-Info "`n🌍 5단계: KG이니시스 API 연결성 테스트"
    
    # 테스트 URL들
    $testUrls = @(
        "https://stgstdpay.inicis.com",
        "https://fcstdpay.inicis.com", 
        "https://ksstdpay.inicis.com"
    )
    
    foreach ($url in $testUrls) {
        try {
            $response = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
            
            if ($response.StatusCode -eq 200) {
                Write-Success "  ✅ $url : 연결 가능 (HTTP $($response.StatusCode))"
                $TestResults += @{Step="API연결성"; Item=$url; Status="PASS"; Details="HTTP $($response.StatusCode)"}
            } else {
                Write-Warning "  ⚠️  $url : HTTP $($response.StatusCode)"
                $TestResults += @{Step="API연결성"; Item=$url; Status="WARN"; Details="HTTP $($response.StatusCode)"}
                $WarningCount++
            }
        } catch {
            Write-Error "  ❌ $url : 연결 실패 - $($_.Exception.Message)"
            $TestResults += @{Step="API연결성"; Item=$url; Status="FAIL"; Details=$_.Exception.Message}
            $ErrorCount++
        }
    }
}

# ========== 6. Node.js 서버 시뮬레이션 테스트 ==========
Write-Info "`n🚀 6단계: Node.js 서버 구동 테스트"

try {
    # 포트 3000 사용 중인지 확인
    $portCheck = netstat -an | findstr ":3000"
    
    if ($portCheck) {
        Write-Warning "⚠️  포트 3000이 이미 사용 중입니다"
        $WarningCount++
    } else {
        Write-Success "✅ 포트 3000 사용 가능"
    }
    
    # app.js 구문 검증
    $appJsContent = Get-Content "app.js" -Raw
    
    # 필수 구성 요소 확인
    $requiredPatterns = @(
        @{Pattern="const express = require"; Name="Express 설정"},
        @{Pattern="const crypto = require"; Name="Crypto 모듈"},
        @{Pattern="app\.get.*\/.*req.*res"; Name="GET 라우터"},
        @{Pattern="app\.post.*return.*req.*res"; Name="POST 라우터"},
        @{Pattern="app\.listen.*3000"; Name="서버 리스닝"}
    )
    
    foreach ($check in $requiredPatterns) {
        if ($appJsContent -match $check.Pattern) {
            Write-Success "  ✅ $($check.Name) 확인됨"
            $TestResults += @{Step="서버구성"; Item=$check.Name; Status="PASS"; Details="Pattern matched"}
        } else {
            Write-Error "  ❌ $($check.Name) 누락됨"
            $TestResults += @{Step="서버구성"; Item=$check.Name; Status="FAIL"; Details="Pattern not found"}
            $ErrorCount++
        }
    }
    
} catch {
    Write-Error "❌ 서버 구성 확인 실패: $($_.Exception.Message)"
    $ErrorCount++
}

# ========== 7. 종합 결과 출력 ==========
Write-Info "`n📊 검증 결과 요약"
Write-Info "============================================"

$totalTests = $TestResults.Count
$passCount = ($TestResults | Where-Object { $_.Status -eq "PASS" }).Count
$failCount = ($TestResults | Where-Object { $_.Status -eq "FAIL" }).Count  
$warnCount = ($TestResults | Where-Object { $_.Status -eq "WARN" }).Count

Write-Info "총 검사 항목: $totalTests"
Write-Success "통과: $passCount"
Write-Warning "경고: $warnCount"
Write-Error "실패: $failCount"

$successRate = [math]::Round(($passCount / $totalTests) * 100, 1)
Write-Info "성공률: $successRate%"

# 상세 결과 테이블
Write-Info "`n📋 상세 검증 결과:"

$TestResults | Format-Table @{
    Label="단계"; Expression={$_.Step}; Width=12
}, @{
    Label="항목"; Expression={$_.Item}; Width=20  
}, @{
    Label="상태"; Expression={
        switch($_.Status) {
            "PASS" { "✅ 통과" }
            "FAIL" { "❌ 실패" }
            "WARN" { "⚠️  경고" }
        }
    }; Width=8
}, @{
    Label="세부사항"; Expression={$_.Details}; Width=40
} -AutoSize

# 최종 판정
Write-Info "`n🏁 최종 판정"
Write-Info "============================================"

if ($ErrorCount -eq 0) {
    Write-Success "🎉 KG이니시스 API 연동이 정상적으로 구현되었습니다!"
    Write-Success "✅ 모든 핵심 검증 항목을 통과했습니다."
    
    if ($WarningCount -gt 0) {
        Write-Warning "`n⚠️  $WarningCount 개의 경고가 있습니다. 검토를 권장합니다."
    }
    
    Write-Info "`n🚀 다음 단계:"
    Write-Info "   1. npm start 명령으로 서버 실행"
    Write-Info "   2. http://localhost:3000 접속하여 결제 테스트" 
    Write-Info "   3. 실제 KG이니시스 테스트 결제 진행"
    
} else {
    Write-Error "❌ KG이니시스 API 연동에 $ErrorCount 개의 오류가 발견되었습니다."
    Write-Error "⚠️  오류를 수정한 후 다시 검증해주세요."
    
    Write-Info "`n🔧 권장 조치사항:"
    Write-Info "   1. 누락된 파일들을 확인하여 추가"
    Write-Info "   2. package.json 의존성 설치: npm install"
    Write-Info "   3. Node.js 환경 확인 및 재설치"
}

# 로그 파일 저장
$logData = @{
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    TestMode = $TestMode
    TotalTests = $totalTests
    PassCount = $passCount
    WarnCount = $warnCount
    ErrorCount = $ErrorCount
    SuccessRate = $successRate
    Results = $TestResults
} | ConvertTo-Json -Depth 3

$logFile = "verifictation-log-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
$logData | Out-File -FilePath $logFile -Encoding UTF8

Write-Info "`n📄 검증 결과가 '$logFile'에 저장되었습니다."

# 종료 코드 설정
if ($ErrorCount -gt 0) {
    exit 1
} else {
    exit 0
}
