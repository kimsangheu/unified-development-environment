#!/usr/bin/env node

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const readline = require('readline');

console.log('🔄 C:\\dev 통합 Git 저장소 설정');
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

async function setupUnifiedRepo() {
    try {
        console.log('📋 현재 상황 분석:');
        console.log('1. C:\\dev\\mcp-pg-payment - 기존 Git 저장소 (Python)');
        console.log('2. D:\\Documents\\PG\\KG이니시스\\... - 별도 Git 저장소 (Node.js)');
        console.log('3. 목표: C:\\dev 전체를 통합 저장소로 설정\n');

        const proceed = await askQuestion('C:\\dev를 통합 저장소로 설정하시겠습니까? (y/N): ');
        if (proceed.toLowerCase() !== 'y' && proceed.toLowerCase() !== 'yes') {
            console.log('🛑 작업이 취소되었습니다.');
            rl.close();
            return;
        }

        console.log('\n🔍 1. C:\\dev로 이동...');
        process.chdir('C:\\dev');
        console.log(`✅ 현재 디렉토리: ${process.cwd()}`);

        console.log('\n🔍 2. 기존 저장소 상태 확인...');
        
        // mcp-pg-payment의 git 상태 확인
        if (fs.existsSync('mcp-pg-payment\\.git')) {
            console.log('📁 mcp-pg-payment에 기존 Git 저장소 발견');
            
            const backupChoice = await askQuestion('기존 저장소를 백업하시겠습니까? (y/N): ');
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

        console.log('\n🔍 3. C:\\dev 루트에 새 Git 저장소 초기화...');
        
        // 기존 .git이 있다면 제거 (루트에)
        if (fs.existsSync('.git')) {
            console.log('🗑️  기존 루트 .git 제거...');
            execSync('rmdir /s /q .git', { stdio: 'inherit' });
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

        console.log('\n🔍 5. .gitignore 파일 생성...');
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
dist/
build/
*.build

# Package files
*.zip
*.tar.gz
*.rar
`;

        fs.writeFileSync('.gitignore', gitignoreContent);
        console.log('✅ .gitignore 파일 생성 완료');

        console.log('\n🔍 6. README.md 생성...');
        const readmeContent = `# Development Environment

이 저장소는 개발 환경의 모든 프로젝트를 포함합니다.

## 프로젝트 구조

### mcp-pg-payment/
- **설명**: MCP Payment Gateway 프로젝트 (Python)
- **기술스택**: Python, aiohttp, MCP

### kg-inicis-node/
- **설명**: KG Inicis 결제 연동 프로젝트 (Node.js)
- **기술스택**: Node.js, Express

### servers/
- **설명**: 서버 관련 파일들

## 시작하기

각 프로젝트별 상세한 설정 방법은 해당 폴더의 README.md를 참조하세요.

## 개발 환경 설정

1. Python 프로젝트: \`mcp-pg-payment/README.md\` 참조
2. Node.js 프로젝트: \`kg-inicis-node/README.md\` 참조

## 버전 관리

- Git을 사용하여 전체 개발 환경을 버전 관리합니다.
- 각 프로젝트별 변경사항을 별도 커밋으로 관리합니다.
`;

        fs.writeFileSync('README.md', readmeContent);
        console.log('✅ README.md 파일 생성 완료');

        console.log('\n🔍 7. Node.js 프로젝트 복사...');
        const copyChoice = await askQuestion('D:\\Documents\\PG\\KG이니시스의 Node.js 프로젝트를 복사하시겠습니까? (y/N): ');
        
        if (copyChoice.toLowerCase() === 'y' || copyChoice.toLowerCase() === 'yes') {
            try {
                console.log('📁 kg-inicis-node 폴더 생성...');
                if (!fs.existsSync('kg-inicis-node')) {
                    fs.mkdirSync('kg-inicis-node');
                }
                
                console.log('📋 Node.js 프로젝트 복사 중...');
                const sourceDir = 'D:\\Documents\\PG\\KG이니시스\\general_pc\\PC 일반결제\\node';
                execSync(`xcopy "${sourceDir}" "kg-inicis-node\\" /E /I /H /Y`, { stdio: 'inherit' });
                
                // 복사된 폴더의 .git 제거
                if (fs.existsSync('kg-inicis-node\\.git')) {
                    console.log('🗑️  복사된 프로젝트의 .git 제거...');
                    execSync('rmdir /s /q "kg-inicis-node\\.git"', { stdio: 'inherit' });
                }
                
                console.log('✅ Node.js 프로젝트 복사 완료');
            } catch (error) {
                console.log('❌ 복사 실패:', error.message);
                console.log('💡 수동으로 파일을 복사해주세요.');
            }
        }

        console.log('\n🔍 8. 원격 저장소 설정...');
        const repoName = 'unified-development-environment';
        console.log(`📍 저장소 이름: ${repoName}`);
        
        try {
            execSync(`git remote add origin https://github.com/kimsangheu/${repoName}.git`, { stdio: 'inherit' });
            console.log('✅ 원격 저장소 연결 완료');
        } catch (error) {
            console.log('❌ 원격 저장소 연결 실패 (이미 존재하거나 네트워크 오류)');
        }

        console.log('\n🔍 9. 첫 번째 커밋 준비...');
        const commitChoice = await askQuestion('모든 파일을 추가하고 첫 번째 커밋을 생성하시겠습니까? (y/N): ');
        
        if (commitChoice.toLowerCase() === 'y' || commitChoice.toLowerCase() === 'yes') {
            try {
                console.log('📝 파일 스테이징...');
                execSync('git add .', { stdio: 'inherit' });
                
                console.log('💾 첫 번째 커밋 생성...');
                execSync('git commit -m "Initial commit: Unified development environment setup"', { stdio: 'inherit' });
                
                console.log('✅ 첫 번째 커밋 완료');
            } catch (error) {
                console.log('❌ 커밋 생성 실패:', error.message);
            }
        }

        console.log('\n🎉 C:\\dev 통합 저장소 설정 완료!');
        console.log('\n📋 다음 단계:');
        console.log(`1. GitHub에서 '${repoName}' 저장소 생성`);
        console.log('2. git push -u origin main (첫 푸시)');
        console.log('3. 각 프로젝트별 README.md 업데이트');
        
        console.log('\n🔗 GitHub 저장소 생성 URL:');
        console.log('https://github.com/new');

    } catch (error) {
        console.error('❌ 예상치 못한 오류:', error.message);
    } finally {
        rl.close();
    }
}

// 실행
setupUnifiedRepo();
