#!/usr/bin/env node

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const readline = require('readline');

console.log('🔄 KG이니시스 Node.js 프로젝트를 mcp-pg-payment로 이동');
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

async function moveKgInicisToMcp() {
    try {
        console.log('📋 이동 계획:');
        console.log('From: D:\\Documents\\PG\\KG이니시스\\general_pc\\PC 일반결제\\node');
        console.log('To: C:\\dev\\mcp-pg-payment\\src\\kg_inicis_node');
        console.log('\n이렇게 하면 논리적으로 올바른 구조가 됩니다:');
        console.log('- Python MCP 서버 + Node.js 실제 구현체 = 통합 PG 솔루션\n');

        const proceed = await askQuestion('이동을 진행하시겠습니까? (y/N): ');
        if (proceed.toLowerCase() !== 'y' && proceed.toLowerCase() !== 'yes') {
            console.log('🛑 작업이 취소되었습니다.');
            rl.close();
            return;
        }

        console.log('\n🔍 1. C:\\dev\\mcp-pg-payment로 이동...');
        process.chdir('C:\\dev\\mcp-pg-payment');
        console.log(`✅ 현재 디렉토리: ${process.cwd()}`);

        console.log('\n🔍 2. src 디렉토리 확인...');
        if (!fs.existsSync('src')) {
            console.log('📁 src 디렉토리 생성...');
            fs.mkdirSync('src');
        }
        console.log('✅ src 디렉토리 준비 완료');

        console.log('\n🔍 3. 대상 폴더 생성...');
        const targetDir = 'src\\kg_inicis_node';
        if (fs.existsSync(targetDir)) {
            console.log(`⚠️  ${targetDir} 폴더가 이미 존재합니다.`);
            const overwrite = await askQuestion('덮어쓰시겠습니까? (y/N): ');
            if (overwrite.toLowerCase() === 'y' || overwrite.toLowerCase() === 'yes') {
                console.log('🗑️  기존 폴더 제거...');
                execSync(`rmdir /s /q "${targetDir}"`, { stdio: 'inherit' });
            } else {
                console.log('🛑 작업이 취소되었습니다.');
                rl.close();
                return;
            }
        }

        console.log(`📁 ${targetDir} 폴더 생성...`);
        fs.mkdirSync(targetDir, { recursive: true });

        console.log('\n🔍 4. KG이니시스 Node.js 프로젝트 이동...');
        const sourceDir = 'D:\\Documents\\PG\\KG이니시스\\general_pc\\PC 일반결제\\node';
        
        try {
            console.log('📋 파일 복사 중...');
            execSync(`xcopy "${sourceDir}" "${targetDir}\\" /E /I /H /Y`, { stdio: 'inherit' });
            console.log('✅ 파일 복사 완료');
            
            // 복사된 폴더의 .git 제거 (통합 저장소에서 관리하기 위해)
            const gitDir = path.join(targetDir, '.git');
            if (fs.existsSync(gitDir)) {
                console.log('🗑️  복사된 프로젝트의 .git 제거...');
                execSync(`rmdir /s /q "${gitDir}"`, { stdio: 'inherit' });
            }
            
            console.log('✅ KG이니시스 프로젝트 이동 완료');
        } catch (error) {
            console.log('❌ 파일 이동 실패:', error.message);
            rl.close();
            return;
        }

        console.log('\n🔍 5. 원본 폴더 정리...');
        const deleteOriginal = await askQuestion('원본 폴더를 삭제하시겠습니까? (y/N): ');
        if (deleteOriginal.toLowerCase() === 'y' || deleteOriginal.toLowerCase() === 'yes') {
            try {
                console.log('🗑️  원본 폴더 삭제...');
                execSync(`rmdir /s /q "${sourceDir}"`, { stdio: 'inherit' });
                console.log('✅ 원본 폴더 삭제 완료');
            } catch (error) {
                console.log('❌ 원본 폴더 삭제 실패:', error.message);
                console.log('💡 수동으로 삭제해주세요.');
            }
        }

        console.log('\n🔍 6. 프로젝트 README.md 업데이트...');
        const updateReadme = await askQuestion('README.md를 업데이트하시겠습니까? (y/N): ');
        if (updateReadme.toLowerCase() === 'y' || updateReadme.toLowerCase() === 'yes') {
            const readmeContent = `# MCP Payment Gateway

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
\`\`\`bash
cd src/mcp_server
pip install -r requirements.txt
python server.py
\`\`\`

### KG이니시스 Node.js
\`\`\`bash
cd src/kg_inicis_node
npm install
node app.js
\`\`\`

## 개발 환경

- Python 3.8+
- Node.js 16+
- 각 PG사별 테스트 계정 필요

## 버전 관리

- Git을 사용하여 통합 프로젝트를 버전 관리합니다.
- Python과 Node.js 구현체를 함께 관리합니다.
`;

            fs.writeFileSync('README.md', readmeContent);
            console.log('✅ README.md 업데이트 완료');
        }

        console.log('\n🔍 7. Git 상태 확인...');
        try {
            const status = execSync('git status --porcelain', { encoding: 'utf8' });
            if (status.trim()) {
                console.log('📝 변경된 파일들:');
                console.log(status);
                
                const commitChanges = await askQuestion('변경사항을 커밋하시겠습니까? (y/N): ');
                if (commitChanges.toLowerCase() === 'y' || commitChanges.toLowerCase() === 'yes') {
                    try {
                        execSync('git add .', { stdio: 'inherit' });
                        execSync('git commit -m "Add KG Inicis Node.js implementation to mcp-pg-payment project"', { stdio: 'inherit' });
                        console.log('✅ 커밋 완료');
                    } catch (error) {
                        console.log('❌ 커밋 실패:', error.message);
                    }
                }
            }
        } catch (error) {
            console.log('⚠️  Git 상태 확인 실패 (Git 저장소가 아닐 수 있음)');
        }

        console.log('\n🎉 KG이니시스 프로젝트 이동 완료!');
        console.log('\n📋 결과:');
        console.log(`✅ 위치: C:\\dev\\mcp-pg-payment\\src\\kg_inicis_node\\`);
        console.log('✅ Python MCP 서버와 Node.js 구현체가 통합됨');
        console.log('\n📋 다음 단계:');
        console.log('1. cd src/kg_inicis_node');
        console.log('2. npm install (의존성 재설치)');
        console.log('3. node app.js (테스트 실행)');
        console.log('4. 통합 프로젝트 GitHub 푸시');

    } catch (error) {
        console.error('❌ 예상치 못한 오류:', error.message);
    } finally {
        rl.close();
    }
}

// 실행
moveKgInicisToMcp();
