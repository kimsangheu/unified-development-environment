# Unified Development Environment

개발 환경의 모든 프로젝트를 통합 관리하는 저장소입니다.

## 📁 프로젝트 구조

### mcp-pg-payment/
- **설명**: MCP Payment Gateway 통합 프로젝트
- **기술스택**: Python + Node.js
- **구성요소**:
  - `src/mcp_server/`: Python MCP 서버 (통합 인터페이스)
  - `src/kg_inicis_node/`: KG이니시스 Node.js 실제 구현체

### servers/
- **설명**: 서버 관련 설정 및 파일들

### backup/
- **설명**: 기존 Git 히스토리 백업

## 🚀 시작하기

### Python MCP 서버
```bash
cd mcp-pg-payment/src/mcp_server
pip install -r requirements.txt
python server.py
```

### KG이니시스 Node.js 서버
```bash
cd mcp-pg-payment/src/kg_inicis_node
npm install
node app.js
```

## 🛠️ 개발 환경

- **Python**: 3.8+
- **Node.js**: 16+
- **Git**: 통합 버전 관리

## 📝 버전 관리

- 전체 개발 환경을 하나의 Git 저장소에서 관리
- 프로젝트별 변경사항을 명확한 커밋 메시지로 구분
- 통합된 이슈 추적 및 문서화

## 🔗 관련 링크

- [KG이니시스 개발 가이드](./mcp-pg-payment/src/kg_inicis_node/README.md)
- [MCP 서버 문서](./mcp-pg-payment/README.md)
