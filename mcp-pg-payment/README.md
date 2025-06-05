# MCP Payment Gateway

통합 결제 게이트웨이 프로젝트입니다.

## 프로젝트 구조

### src/mcp_server/
- **설명**: MCP (Model Context Protocol) 서버 구현
- **기술스택**: Python, aiohttp, MCP
- **기능**: 다양한 PG사 연동을 위한 통합 인터페이스 제공

### src/kg_inicis_node/
- **설명**: KG이니시스 실제 API 연동 구현체
- **기술스택**: Node.js, Express
- **기능**: KG이니시스 실제 결제 API 연동 및 암호화 처리

## 시작하기

### Python MCP 서버
```bash
cd src/mcp_server
pip install -r requirements.txt
python server.py
```

### KG이니시스 Node.js
```bash
cd src/kg_inicis_node
npm install
node app.js
```

## 개발 환경

- Python 3.8+
- Node.js 16+
- 각 PG사별 테스트 계정 필요

## 버전 관리

- Git을 사용하여 통합 프로젝트를 버전 관리합니다.
- Python과 Node.js 구현체를 함께 관리합니다.
