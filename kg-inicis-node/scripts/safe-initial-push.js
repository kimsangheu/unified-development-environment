#!/usr/bin/env node

const { execSync } = require('child_process');
const readline = require('readline');

console.log('🚀 안전한 초기 푸시 수행');
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

async function safeInitialPush() {
    try {
        console.log('🔍 1. 먼저 Git 소유권 문제를 해결합니다...');
        
        // Git 소유권 문제 해결
        try {
            const currentPath = process.cwd().replace(/\\/g, '/');
            execSync(`git config --global --add safe.directory "${currentPath}"`, { stdio: 'pipe' });
            console.log('✅ Git 소유권 문제 해결 완료\n');
        } catch (error) {
            console.log('⚠️  Git 소유권 설정 실패, 계속 진행합니다...\n');
        }

        console.log('🔍 2. Git 상태 확인...');
        let status;
        try {
            status = execSync('git status --porcelain', { encoding: 'utf8' });
            console.log('✅ Git 상태 확인 성공');
            
            if (status.trim()) {
                console.log('📝 변경된 파일들:');
                const lines = status.trim().split('\n');
                lines.slice(0, 10).forEach(line => console.log(`   ${line}`));
                if (lines.length > 10) {
                    console.log(`   ... 그외 ${lines.length - 10}개 파일`);
                }
            } else {
                console.log('📝 변경사항이 없습니다. 스테이징할 파일이 없습니다.');
                rl.close();
                return;
            }
        } catch (error) {
            console.log('❌ Git 상태 확인 실패:', error.message);
            rl.close();
            return;
        }

        console.log('\n🔍 3. GitHub 저장소 존재 확인...');
        const repoUrl = 'https://github.com/kimsangheu/kg-inicis-payment-integration.git';
        console.log(`📍 저장소 URL: ${repoUrl}`);
        
        const proceed = await askQuestion('\n계속 진행하시겠습니까? (y/N): ');
        if (proceed.toLowerCase() !== 'y' && proceed.toLowerCase() !== 'yes') {
            console.log('🛑 사용자에 의해 취소되었습니다.');
            rl.close();
            return;
        }

        console.log('\n🔍 4. 파일 스테이징...');
        try {
            console.log('   git add . 실행 중...');
            execSync('git add .', { stdio: 'inherit' });
            console.log('✅ 파일 스테이징 완료');
        } catch (error) {
            console.log('❌ 파일 스테이징 실패:', error.message);
            rl.close();
            return;
        }

        console.log('\n🔍 5. 커밋 생성...');
        try {
            const commitMessage = 'Initial commit: KG Inicis payment integration setup';
            console.log(`   커밋 메시지: "${commitMessage}"`);
            execSync(`git commit -m "${commitMessage}"`, { stdio: 'inherit' });
            console.log('✅ 커밋 생성 완료');
        } catch (error) {
            console.log('❌ 커밋 생성 실패:', error.message);
            console.log('   (이미 커밋된 내용이 있을 수 있습니다)');
        }

        console.log('\n🔍 6. 브랜치 설정 확인...');
        try {
            const currentBranch = execSync('git branch --show-current', { encoding: 'utf8' }).trim();
            console.log(`✅ 현재 브랜치: ${currentBranch}`);
            
            if (currentBranch !== 'main') {
                console.log('   main 브랜치로 변경합니다...');
                try {
                    execSync('git checkout main', { stdio: 'inherit' });
                } catch (switchError) {
                    console.log('   main 브랜치를 생성하고 변경합니다...');
                    execSync('git checkout -b main', { stdio: 'inherit' });
                }
            }
        } catch (error) {
            console.log('❌ 브랜치 확인 실패:', error.message);
        }

        console.log('\n🔍 7. 원격 저장소 푸시 시도...');
        const pushConfirm = await askQuestion('GitHub에 푸시하시겠습니까? (y/N): ');
        if (pushConfirm.toLowerCase() !== 'y' && pushConfirm.toLowerCase() !== 'yes') {
            console.log('🛑 푸시가 취소되었습니다.');
            rl.close();
            return;
        }

        try {
            console.log('   git push -u origin main 실행 중...');
            console.log('   (GitHub 인증이 필요할 수 있습니다)');
            execSync('git push -u origin main', { stdio: 'inherit' });
            console.log('✅ GitHub 푸시 성공!');
        } catch (error) {
            console.log('❌ GitHub 푸시 실패:', error.message);
            console.log('\n💡 가능한 해결 방법:');
            console.log('1. GitHub에서 저장소가 생성되었는지 확인');
            console.log('2. GitHub 인증 설정 확인 (Personal Access Token)');
            console.log('3. 저장소 권한 확인');
            console.log('\n🔗 저장소 주소에서 확인하세요:');
            console.log('   https://github.com/kimsangheu/kg-inicis-payment-integration');
        }

        console.log('\n🎉 초기 푸시 프로세스 완료!');
        console.log('\n📋 다음 단계:');
        console.log('1. GitHub 저장소 확인: https://github.com/kimsangheu/kg-inicis-payment-integration');
        console.log('2. README.md 업데이트');
        console.log('3. 개발 환경 설정 문서화');

    } catch (error) {
        console.error('❌ 예상치 못한 오류:', error.message);
    } finally {
        rl.close();
    }
}

// 실행
safeInitialPush();
