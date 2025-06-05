# KG이니시스 PG연동 프로젝트

## 프로젝트 개요

Node.js + Express 기반의 KG이니시스 결제 게이트웨이 연동 시스템입니다.

### 기술 스택
- **Backend**: Node.js + Express.js
- **Template Engine**: EJS
- **암호화**: crypto 모듈 (SHA256)
- **HTTP Client**: request 모듈
- **PG사**: KG이니시스

## Git 브랜치 전략

### 브랜치 구조
```
main (운영)
├── develop (개발 통합)
├── feature/* (기능 개발)
└── hotfix/* (긴급 수정)
```

### 브랜치 역할
- **main**: 운영 환경 배포 브랜치
- **develop**: 개발 통합 브랜치, 모든 기능이 병합되는 지점
- **feature/***: 개별 기능 개발 브랜치
- **hotfix/***: 운영 환경 긴급 수정 브랜치

### 워크플로우
1. `develop`에서 `feature/기능명` 브랜치 생성
2. 기능 개발 완료 후 `develop`으로 병합
3. `develop`에서 테스트 완료 후 `main`으로 병합
4. `main`에서 운영 배포

## 자동화 시스템

### 검증 단계
1. **1단계**: 문법 및 구조 검증
2. **2단계**: API 연동 및 암호화 검증
3. **3단계**: 보안 및 통합 검증

### Git 자동 커밋
- 각 검증 단계 완료 시 자동 커밋
- 커밋 메시지 형식: `[STEP-{번호}] {작업내용} - {날짜}`

## 검증 및 테스트

### PowerShell 검증 스크립트

KG이니시스 API 연동이 제대로 구현되었는지 검증할 수 있는 PowerShell 스크립트들이 제공됩니다.

#### 🚀 빠른 실행 (추천)
```batch
# 배치 파일로 간편 실행
scripts\검증실행.bat
```

#### 📋 개별 스크립트 실행

**1. 빠른 검증**
```powershell
.\scripts\Quick-Check.ps1
```
- 필수 파일 존재 확인
- Node.js 환경 검증
- 기본 암호화 로직 테스트
- 포트 사용 상태 확인

**2. 전체 검증**
```powershell
.\scripts\Verify-KGInicisAPI.ps1
```
- 프로젝트 파일 구조 검증
- package.json 의존성 확인
- SHA256 암호화 로직 테스트
- API URL 설정 검증
- KG이니시스 서버 연결성 테스트
- Node.js 서버 구성 검증

**3. API 연결 테스트**
```powershell
.\scripts\Test-KGInicisAPI.ps1 -TestType connection
.\scripts\Test-KGInicisAPI.ps1 -TestType payment
.\scripts\Test-KGInicisAPI.ps1 -TestType full
```
- KG이니시스 테스트 서버 연결성 확인
- 암호화 및 서명 로직 검증
- properties.js 모듈 테스트

**4. 실제 결제 테스트**
```powershell
.\scripts\Test-Payment.ps1
.\scripts\Test-Payment.ps1 -Amount 2000 -AutoBrowser
```
- 실제 결제 프로세스 시뮬레이션
- 브라우저 자동 실행
- 결제 데이터 생성 및 검증

### 🔍 검증 결과 해석

- ✅ **통과**: 해당 항목이 정상적으로 구현됨
- ⚠️ **경고**: 기능은 동작하지만 개선이 필요함  
- ❌ **실패**: 오류가 발견되어 수정이 필요함

### 📊 검증 보고서

검증 완료 후 다음 파일들이 자동 생성됩니다:
- `verifictation-log-YYYYMMDD-HHMMSS.json`: 상세 검증 결과
- 콘솔 출력: 실시간 검증 진행 상황

### 🛠 문제 해결

**일반적인 문제:**
- PowerShell 실행 정책 오류: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Node.js 미설치: [Node.js 공식 사이트](https://nodejs.org)에서 설치
- 포트 3000 충돌: `netstat -ano | findstr :3000`으로 프로세스 확인 후 종료

## 보안 주의사항
- 운영 환경 키/토큰은 환경변수로 관리
- 테스트용 signKey: `SU5JTElURV9UUklQTEVERVNfS0VZU1RS`
- 민감 정보는 절대 소스코드에 하드코딩 금지

## 문의
- 개발팀: [연락처]
- 문서 최종 업데이트: 2025-06-05
