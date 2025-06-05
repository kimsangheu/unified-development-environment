# KG이니시스 PG연동 프로젝트 개발 가이드라인

## 프로젝트 개요

### 기술 스택
- **Backend**: Node.js + Express.js
- **Template Engine**: EJS
- **암호화**: crypto 모듈 (SHA256)
- **HTTP Client**: request 모듈
- **PG사**: KG이니시스

### 핵심 기능
- 결제 요청/응답 처리
- SHA256 암호화 검증
- API 인증 토큰 관리
- 망취소 처리

## 파일 구조 및 역할

### 핵심 파일 구조
```
/node/
├── app.js                    # 메인 Express 서버
├── properties.js             # API URL 설정 모듈
├── package.json              # 의존성 관리
├── shrimp-rules.md          # 프로젝트 표준 (본 파일)
└── views/
    ├── INIstdpay_pc_req.html    # 결제 요청 페이지
    └── INIstdpay_pc_return.ejs  # 결제 응답 페이지
```

### 파일별 수정 규칙
- **app.js 수정 시**: 암호화 로직, 라우터 설정, 에러 처리 검증 필수
- **properties.js 수정 시**: URL 검증 및 환경별 분리 확인 필수
- **views 파일 수정 시**: 보안 필드 노출 여부 검토 필수

## 코드 표준

### 암호화 처리 규칙
- **SHA256 해시 사용 필수**: `crypto.createHash("sha256")`
- **mKey 생성 패턴**: `crypto.createHash("sha256").update(signKey).digest('hex')`
- **signature 생성**: `oid + price + timestamp` 조합
- **verification 생성**: `oid + price + signKey + timestamp` 조합
- **타임스탬프**: `new Date().getTime()` 사용 필수

### API 엔드포인트 규칙
- **GET /**: 결제 요청 페이지 렌더링
- **POST /INIstdpay_pc_return.ejs**: 결제 응답 처리
- **GET /close**: 결제창 닫기 스크립트 제공
- **새로운 엔드포인트 추가 시**: 반드시 암호화 검증 포함

### 에러 처리 표준
- **try-catch 블록 필수**: 모든 API 호출에 적용
- **망취소 처리**: 예외 발생 시 `netCancelUrl` 호출
- **에러 로깅**: `console.log(e)` 형태로 기록
- **민감 정보 로깅 금지**: 키, 토큰 등 보안 정보 제외

### 변수 명명 규칙
- **camelCase 사용**: mid, authToken, netCancelUrl
- **상수는 대문자**: MOID, TotPrice
- **암호화 관련**: mKey, signKey, signature, verification

## Git 워크플로우

### 브랜치 전략
- **main**: 운영 배포 브랜치
- **develop**: 개발 통합 브랜치  
- **feature/***: 기능별 개발 브랜치
- **hotfix/***: 긴급 수정 브랜치

### 자동 커밋 규칙
- **단계 완료 시 자동 커밋**: 각 작업 단계 완료 후 즉시 커밋
- **커밋 메시지 형식**: `[STEP-{번호}] {작업내용} - {날짜}`
- **커밋 전 검증**: 문법 오류, 보안 키 노출 검사

### 커밋 메시지 패턴
- `feat: 새로운 기능 추가`
- `fix: 버그 수정`
- `security: 보안 관련 수정`
- `test: 테스트 코드 추가/수정`
- `docs: 문서 수정`

## 검증 및 테스트

### 자동 검증 스크립트
- **API 연결성 테스트**: properties.js URL 유효성 검증
- **암호화 검증**: SHA256 해시 생성/검증 테스트
- **환경변수 검증**: 필수 설정값 존재 여부 확인
- **코드 품질 검증**: ESLint 규칙 적용

### 3단계 검증 프로세스
1. **1단계**: 코드 문법 및 구조 검증
2. **2단계**: API 연동 및 암호화 검증  
3. **3단계**: 통합 테스트 및 보안 검증

### 검증 스크립트 실행 규칙
- **Node.js 기반**: PowerShell 대신 JavaScript 검증 스크립트 사용
- **단계별 실행**: 이전 단계 통과 후 다음 단계 진행
- **실패 시 중단**: 검증 실패 시 다음 단계 진행 금지

## 환경 관리

### 환경별 설정
- **테스트 환경**: `stgstdpay.inicis.com` 사용
- **운영 환경**: `stdpay.inicis.com` 사용
- **IDC 구분**: fc, ks, stg 지원

### JavaScript 파일 관리
- **테스트**: `https://stgstdpay.inicis.com/stdjs/INIStdPay.js`
- **운영**: `https://stdpay.inicis.com/stdjs/INIStdPay.js`
- **환경 전환 시**: 반드시 JavaScript 파일도 함께 변경

### 포트 및 URL 설정
- **기본 포트**: 3000
- **로컬 테스트**: `http://localhost:3000`
- **returnUrl**: `/INIstdpay_pc_return.ejs`
- **closeUrl**: `/close`

## 보안 규칙

### 중요 보안 필드
- **signKey**: `SU5JTElURV9UUklQTEVERVNfS0VZU1RS` (테스트용)
- **mid**: 상점 아이디 (INIpayTest)
- **authToken**: 승인 요청 토큰
- **timestamp**: 타임스탬프 (Long형)

### 보안 검증 필수사항
- **서명 검증**: signature와 verification 이중 검증
- **타임스탬프 검증**: 유효 시간 범위 확인
- **URL 검증**: authUrl과 authUrl2 일치성 확인
- **토큰 유효성**: authToken 형식 및 만료 시간 확인

### 민감 정보 처리
- **로그 출력 금지**: signKey, authToken 등
- **하드코딩 금지**: 운영용 키/토큰 소스코드 포함 금지
- **HTTPS 필수**: 운영 환경에서 HTTP 사용 금지

## AI 에이전트 결정 기준

### 파일 수정 우선순위
1. **높음**: app.js, properties.js
2. **중간**: package.json, 검증 스크립트
3. **낮음**: views 템플릿 파일

### 충돌 해결 규칙
- **보안 vs 기능**: 항상 보안 우선
- **테스트 vs 운영**: 명시적 지시 없으면 테스트 환경 우선
- **자동화 vs 수동**: 자동화 우선 (단, 검증 필수)

### 의존성 관리
- **기존 모듈 우선**: 새로운 의존성 최소화
- **보안 취약점**: 정기적 취약점 검사 필요
- **버전 고정**: package.json에서 정확한 버전 명시

## 금지 사항

### 절대 금지
- **운영 키 하드코딩**: 소스코드에 실제 운영 키 포함
- **HTTP 운영 사용**: 운영 환경에서 HTTP 프로토콜 사용
- **에러 무시**: try-catch 없는 API 호출
- **검증 생략**: 암호화 검증 과정 생략
- **민감 정보 로깅**: 키, 토큰, 개인정보 로그 출력

### 주의 사항
- **환경 혼용**: 테스트/운영 설정 혼재 사용 금지
- **타임스탬프 재사용**: 동일한 timestamp 중복 사용 금지
- **URL 직접 수정**: properties.js 우회하여 URL 직접 설정 금지
- **인코딩 변경**: charset="UTF-8" 설정 임의 변경 금지

### 코드 품질
- **console.log 과다 사용 금지**: 디버깅 로그는 개발 완료 후 제거
- **전역 변수 사용 금지**: 함수 스코프 내 변수 선언 필수  
- **동기 처리 강요 금지**: 비동기 패턴 유지 필수
- **에러 메시지 노출**: 사용자에게 내부 에러 상세 노출 금지

## 작업 완료 체크리스트

### 각 단계 완료 시 확인사항
- [ ] 코드 문법 오류 없음
- [ ] 보안 필드 하드코딩 없음  
- [ ] 테스트 실행 성공
- [ ] Git 커밋 완료
- [ ] 문서 업데이트 완료

### 최종 배포 전 확인사항
- [ ] 운영/테스트 환경 설정 확인
- [ ] JavaScript 파일 URL 일치 확인
- [ ] 암호화 검증 로직 확인
- [ ] 에러 처리 로직 확인
- [ ] 보안 검증 완료