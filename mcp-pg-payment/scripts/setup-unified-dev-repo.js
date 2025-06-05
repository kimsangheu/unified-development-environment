#!/usr/bin/env node

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const readline = require('readline');

console.log('🔄 C:\\dev 전체를 통합 Git 저장소로 설정');
console.log('================================\n');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

function askQuestion(question) {
    return new Promise((resolve) => {
        rl.question(question, (answer) => {
            resolve(answer);
        });
    });
}

async function setupUnifiedDevRepo() {
    try {
        console.log('📋 통합 저장소 설정 계획:');
        console.log('1. C:\\dev를 루트 Git 저장소로 설정');
        console.log('2. mcp-pg-payment의 Git 히스토리 백업');
        console.log('3. 통합 .gitignore 및 README.md 생성');
        console.log('4. 모든 개발 파일을 한 곳에서 관리\n');

        const proceed = await askQuestion('C:\\dev 통합 저장소 설정을 진행하시겠습니까? (y/N): ');
        if (proceed.toLowerCase() !== 'y' && proceed.toLowerCase() !== 'yes') {
            console.log('🛑 작업이 취소되었습니다.');
            rl.close();
            return;
        }

        console.log('\n🔍 1. C:\\dev로 이동...');
        process.chdir('C:\\dev');
        console.log(`✅ 현재 디렉토리: ${process.cwd()}`);

        console.log('\n🔍 2. 기존 Git 저장소 백업...');
        
        // mcp-pg-payment의 Git 히스토리 백업
        if (fs.existsSync('mcp-pg-payment\\.git')) {
            console.log('📁 mcp-pg-payment Git 히스토리 발견');
            
            const backupChoice = await askQuestion('mcp-pg-payment Git 히스토리를 백업하시겠습니까? (y/N): ');
            if (backupChoice.toLowerCase() === 'y' || backupChoice.toLowerCase() === 'yes') {
                console.log('💾 Git 히스토리 백업 중...');
                try {
                    if (!fs.existsSync('backup')) {
                        fs.mkdirSync('backup');
                    }
                    execSync('xcopy "mcp-pg-payment\\.git" "backup\\mcp-pg-payment-git-backup\\" /E /I /H', { stdio: 'inherit' });
                    console.log('✅ 백업 완료: backup\\mcp-pg-payment-git-backup\\');
                } catch (error) {
                    console.log('❌ 백업 실패:', error.message);
                }
            }
        }

        console.log('\n🔍 3. C:\\dev 루트 Git 저장소 초기화...');
        
        // 기존 루트 .git이 있다면 제거
        if (fs.existsSync('.git')) {
            console.log('🗑️  기존 루트 .git 제거...');
            execSync('rmdir /s /q .git', { stdio: 'inherit' });
        }

        // mcp-pg-payment의 .git 제거
        if (fs.existsSync('mcp-pg-payment\\.git')) {
            console.log('🗑️  mcp-pg-payment .git 제거...');
            execSync('rmdir /s /q "mcp-pg-payment\\.git"', { stdio: 'inherit' });
        }

        // 새 Git 저장소 초기화
        console.log('🆕 새 Git 저장소 초기화...');
        execSync('git init', { stdio: 'inherit' });
        
        console.log('\n🔍 4. Git 사용자 정보 설정...');
        try {
            execSync('git config user.name "KG Inicis Developer"', { stdio: 'inherit' });
            execSync('git config user.email "kimsangheu@gmail.com"', { stdio: 'inherit' });
            console.log('✅ Git 사용자 정보 설정 완료');
        } catch (error) {
            console.log('❌ Git 사용자 정보 설정 실패:', error.message);
        }

        console.log('\n🔍 5. 통합 .gitignore 파일 생성...');
        const gitignoreContent = `# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.env
*.egg-info/
dist/
build/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.node_repl_history

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp
.tmp/

# Backup files
backup/
*.backup
*.bak

# Build outputs
*.build

# Package files
*.zip
*.tar.gz
*.rar

# Development specific
.env.local
.env.development
.env.test
.env.production
`;

        fs.writeFileSync('.gitignore', gitignoreContent);
        console.log('✅ 통합 .gitignore 파일 생성 완료');

        console.log('\n🔍 6. 통합 README.md 생성...');
        const readmeContent = `# Unified Development Environment

개발 환경의 모든 프로젝트를 통합 관리하는 저장소입니다.

## 📁 프로젝트 구조

### mcp-pg-payment/
- **설명**: MCP Payment Gateway 통합 프로젝트
- **기술스택**: Python + Node.js
- **구성요소**:
  - \`src/mcp_server/\`: Python MCP 서버 (통합 인터페이스)
  - \`src/kg_inicis_node/\`: KG이니시스 Node.js 실제 구현체

### servers/
- **설명**: 서버 관련 설정 및 파일들

### backup/
- **설명**: 기존 Git 히스토리 백업

## 🚀 시작하기

### Python MCP 서버
\`\`\`bash
cd mcp-pg-payment/src/mcp_server
pip install -r requirements.txt
python server.py
\`\`\`

### KG이니시스 Node.js 서버
\`\`\`bash
cd mcp-pg-payment/src/kg_inicis_node
npm install
node app.js
\`\`\`

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
`;

        fs.writeFileSync('README.md', readmeContent);
        console.log('✅ 통합 README.md 생성 완료');

        console.log('\n🔍 7. 원격 저장소 설정...');
        const repoName = 'unified-development-environment';
        console.log(`📍 저장소 이름: ${repoName}`);
        
        try {
            execSync(`git remote add origin https://github.com/kimsangheu/${repoName}.git`, { stdio: 'inherit' });
            console.log('✅ 원격 저장소 연결 완료');
        } catch (error) {
            console.log('❌ 원격 저장소 연결 실패 (이미 존재하거나 아직 생성되지 않음)');
        }

        console.log('\n🔍 8. 첫 번째 통합 커밋...');
        const commitChoice = await askQuestion('모든 개발 파일을 통합 커밋하시겠습니까? (y/N): ');
        
        if (commitChoice.toLowerCase() === 'y' || commitChoice.toLowerCase() === 'yes') {
            try {
                console.log('📝 파일 스테이징...');
                execSync('git add .', { stdio: 'inherit' });
                
                console.log('💾 통합 커밋 생성...');
                execSync('git commit -m "Initial commit: Unified development environment with integrated PG projects"', { stdio: 'inherit' });
                
                console.log('✅ 통합 커밋 완료');
            } catch (error) {
                console.log('❌ 커밋 생성 실패:', error.message);
            }
        }

        console.log('\n🎉 C:\\dev 통합 저장소 설정 완료!');
        console.log('\n📋 결과:');
        console.log('✅ C:\\dev 전체가 하나의 Git 저장소로 통합됨');
        console.log('✅ mcp-pg-payment + kg_inicis_node가 포함됨');
        console.log('✅ 모든 개발 파일이 통합 관리됨');
        
        console.log('\n📋 다음 단계:');
        console.log(`1. GitHub에서 '${repoName}' 저장소 생성`);
        console.log('2. git push -u origin main (첫 푸시)');
        console.log('3. 통합 개발 환경 완성! 🎯');
        
        console.log('\n🔗 GitHub 저장소 생성 URL:');
        console.log('https://github.com/new');

    } catch (error) {
        console.error('❌ 예상치 못한 오류:', error.message);
    } finally {
        rl.close();
    }
}

// 실행
setupUnifiedDevRepo();
