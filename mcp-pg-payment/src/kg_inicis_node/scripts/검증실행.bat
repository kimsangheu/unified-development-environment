@echo off
chcp 65001 >nul
title KG이니시스 검증 스크립트 실행기

echo.
echo ===============================================
echo    KG이니시스 PG연동 검증 스크립트 실행기
echo ===============================================
echo.

cd /d "D:\Documents\PG\KG이니시스\general_pc\PC 일반결제\node"

:MENU
echo 🔍 검증 옵션을 선택해주세요:
echo.
echo [1] 빠른 검증 (Quick Check)
echo [2] 전체 검증 (Full Verification)  
echo [3] API 연결 테스트
echo [4] 결제 테스트 시뮬레이션
echo [5] 서버 시작
echo [6] 종료
echo.
set /p choice="선택하세요 (1-6): "

if "%choice%"=="1" goto QUICK_CHECK
if "%choice%"=="2" goto FULL_VERIFICATION
if "%choice%"=="3" goto API_TEST
if "%choice%"=="4" goto PAYMENT_TEST
if "%choice%"=="5" goto START_SERVER
if "%choice%"=="6" goto EXIT

echo ❌ 잘못된 선택입니다. 다시 선택해주세요.
echo.
goto MENU

:QUICK_CHECK
echo.
echo 🚀 빠른 검증을 시작합니다...
echo.
powershell -ExecutionPolicy Bypass -File ".\scripts\Quick-Check.ps1"
echo.
pause
goto MENU

:FULL_VERIFICATION
echo.
echo 🔍 전체 검증을 시작합니다...
echo.
powershell -ExecutionPolicy Bypass -File ".\scripts\Verify-KGInicisAPI.ps1"
echo.
pause
goto MENU

:API_TEST
echo.
echo 🌐 API 연결 테스트를 시작합니다...
echo.
powershell -ExecutionPolicy Bypass -File ".\scripts\Test-KGInicisAPI.ps1" -TestType "connection"
echo.
pause
goto MENU

:PAYMENT_TEST
echo.
echo 💳 결제 테스트 시뮬레이션을 시작합니다...
echo.
powershell -ExecutionPolicy Bypass -File ".\scripts\Test-Payment.ps1" -AutoBrowser
echo.
pause
goto MENU

:START_SERVER
echo.
echo 🚀 Node.js 서버를 시작합니다...
echo 브라우저에서 http://localhost:3000 으로 접속하세요
echo 서버를 중지하려면 Ctrl+C를 누르세요
echo.
npm start
pause
goto MENU

:EXIT
echo.
echo 👋 검증 스크립트를 종료합니다.
echo.
exit /b 0
