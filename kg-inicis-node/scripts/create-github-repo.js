#!/usr/bin/env node

const { execSync } = require('child_process');
const readline = require('readline');

console.log('🏗️  GitHub 저장소 생성 도구');
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

async function createGitHubRepo() {
    try {
        console.log('🔍 GitHub CLI 설치 확인...');
        
        try {
            const ghVersion = execSync('gh --version', { encoding: 'utf8' });
            console.log('✅ GitHub CLI 확인됨');
            console.log(`   버전: ${ghVersion.split('\n')[0]}`);
        } catch (error) {
            console.log('❌ GitHub CLI가 설치되지 않았습니다.');
            console.log('\n💡 GitHub CLI 설치 방법:');
            console.log('1. https://cli.github.com/ 방문');
            console.log('2. Windows용 GitHub CLI 다운로드 및 설치');
            console.log('3. PowerShell에서 "gh auth login" 실행하여 인증');
            console.log('\n또는 수동으로 GitHub 웹사이트에서 저장소를 생성하세요:');
            console.log('https://github.com/new');
            rl.close();
            return;
        }

        console.log('\n🔍 GitHub 인증 상태 확인...');
        try {
            const authStatus = execSync('gh auth status', { encoding: 'utf8', stdio: 'pipe' });
            console.log('✅ GitHub 인증 확인됨');
        } catch (error) {
            console.log('❌ GitHub 인증이 필요합니다.');
            console.log('\n다음 명령을 실행하여 인증하세요:');
            console.log('gh auth login');
            rl.close();
            return;
        }

        console.log('\n🏗️  저장소 생성 정보:');
        console.log('   저장소 이름: kg-inicis-payment-integration');
        console.log('   설명: KG Inicis Payment Integration for Node.js');
        console.log('   공개/비공개: 공개 (public)');
        
        const createConfirm = await askQuestion('\nGitHub 저장소를 생성하시겠습니까? (y/N): ');
        if (createConfirm.toLowerCase() !== 'y' && createConfirm.toLowerCase() !== 'yes') {
            console.log('🛑 저장소 생성이 취소되었습니다.');
            rl.close();
            return;
        }

        console.log('\n🚀 GitHub 저장소 생성 중...');
        try {
            const createCommand = 'gh repo create kg-inicis-payment-integration --public --description "KG Inicis Payment Integration for Node.js" --confirm';
            execSync(createCommand, { stdio: 'inherit' });
            console.log('✅ GitHub 저장소 생성 완료!');
            
            console.log('\n🔗 저장소 정보:');
            console.log('   URL: https://github.com/kimsangheu/kg-inicis-payment-integration');
            console.log('   Clone URL: https://github.com/kimsangheu/kg-inicis-payment-integration.git');
            
            console.log('\n🎉 이제 다음 명령으로 초기 푸시를 진행할 수 있습니다:');
            console.log('node scripts/safe-initial-push.js');
            
        } catch (error) {
            console.log('❌ 저장소 생성 실패:', error.message);
            console.log('\n💡 수동으로 생성하세요:');
            console.log('1. https://github.com/new 방문');
            console.log('2. Repository name: kg-inicis-payment-integration');
            console.log('3. 비어있는 저장소로 생성');
        }

    } catch (error) {
        console.error('❌ 예상치 못한 오류:', error.message);
    } finally {
        rl.close();
    }
}

// 실행
createGitHubRepo();
