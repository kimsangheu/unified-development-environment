const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// GitHub 저장소 정보
const GITHUB_CONFIG = {
    username: 'kimsangheu',
    repoName: 'kg-inicis-payment-integration',
    httpsUrl: 'https://github.com/kimsangheu/kg-inicis-payment-integration.git'
};

// Git 명령어 실행 함수
function runGitCommand(command, description) {
    console.log(`🔧 ${description}...`);
    try {
        const result = execSync(command, { 
            encoding: 'utf8', 
            stdio: 'pipe',
            cwd: process.cwd()
        });
        console.log(`✅ ${description} 성공`);
        if (result.trim()) {
            console.log(`   결과: ${result.trim()}`);
        }
        return result.trim();
    } catch (error) {
        console.error(`❌ ${description} 실패`);
        console.error(`   오류: ${error.message}`);
        if (error.stdout) {
            console.log(`   표준 출력: ${error.stdout}`);
        }
        if (error.stderr) {
            console.error(`   표준 오류: ${error.stderr}`);
        }
        return null;
    }
}

// 메인 Git 원격 저장소 설정 함수
function setupGitRemote() {
    console.log('🚀 Git 원격 저장소 연결을 시작합니다...');
    console.log('================================');
    
    try {
        // 1. 현재 Git 상태 확인
        console.log('📋 1단계: 현재 Git 상태 확인');
        
        const gitStatus = runGitCommand('git status --porcelain', 'Git 작업 디렉토리 상태 확인');
        if (gitStatus === null) {
            throw new Error('Git 저장소가 아니거나 Git이 설치되지 않았습니다.');
        }
        
        const gitLog = runGitCommand('git log --oneline -5', '최근 커밋 히스토리 확인');
        
        // 2. 기존 원격 저장소 확인
        console.log('\n📋 2단계: 기존 원격 저장소 확인');
        
        const existingRemotes = runGitCommand('git remote -v', '기존 원격 저장소 목록 확인');
        
        if (existingRemotes && existingRemotes.includes('origin')) {
            console.log('⚠️  기존 origin 원격 저장소가 존재합니다.');
            console.log('기존 설정을 제거하고 새로 설정합니다...');
            runGitCommand('git remote remove origin', '기존 origin 제거');
        }
        
        // 3. GitHub 원격 저장소 추가
        console.log('\n📋 3단계: GitHub 원격 저장소 추가');
        
        const addRemoteResult = runGitCommand(
            `git remote add origin ${GITHUB_CONFIG.httpsUrl}`, 
            'GitHub 원격 저장소 추가'
        );
        
        if (addRemoteResult === null) {
            throw new Error('원격 저장소 추가에 실패했습니다.');
        }
        
        // 4. 원격 저장소 연결 확인
        console.log('\n📋 4단계: 원격 저장소 연결 확인');
        
        const remoteVerify = runGitCommand('git remote -v', '원격 저장소 연결 상태 확인');
        
        if (!remoteVerify || !remoteVerify.includes(GITHUB_CONFIG.httpsUrl)) {
            throw new Error('원격 저장소 연결 확인에 실패했습니다.');
        }
        
        // 5. 브랜치 설정 확인
        console.log('\n📋 5단계: 브랜치 설정 확인');
        
        const currentBranch = runGitCommand('git branch --show-current', '현재 브랜치 확인');
        
        if (currentBranch === null || currentBranch === '') {
            console.log('현재 브랜치가 없습니다. main 브랜치를 생성합니다...');
            runGitCommand('git checkout -b main', 'main 브랜치 생성 및 전환');
        } else {
            console.log(`현재 브랜치: ${currentBranch}`);
        }
        
        // 6. Git 사용자 정보 확인 및 설정
        console.log('\n📋 6단계: Git 사용자 정보 확인');
        
        const userName = runGitCommand('git config user.name', 'Git 사용자 이름 확인');
        const userEmail = runGitCommand('git config user.email', 'Git 사용자 이메일 확인');
        
        if (!userName || userName === 'PG Developer') {
            console.log('Git 사용자 이름을 업데이트합니다...');
            runGitCommand('git config user.name "KG Inicis Developer"', 'Git 사용자 이름 설정');
        }
        
        if (!userEmail || userEmail === 'developer@example.com') {
            console.log('Git 사용자 이메일을 업데이트합니다...');
            runGitCommand('git config user.email "kimsangheu@gmail.com"', 'Git 사용자 이메일 설정');
        }
        
        // 7. 원격 저장소 연결 테스트
        console.log('\n📋 7단계: 원격 저장소 연결 테스트');
        
        // GitHub에서 기본 브랜치 정보 확인
        runGitCommand('git ls-remote origin', '원격 저장소 접근 테스트');
        
        // 8. 최종 결과 출력
        console.log('\n🎉 Git 원격 저장소 연결 완료!');
        console.log('================================');
        console.log(`📁 로컬 저장소: ${process.cwd()}`);
        console.log(`🔗 원격 저장소: ${GITHUB_CONFIG.httpsUrl}`);
        console.log(`👤 사용자: ${GITHUB_CONFIG.username}`);
        console.log(`📊 현재 브랜치: ${runGitCommand('git branch --show-current', '') || 'main'}`);
        
        console.log('\n🚀 다음 단계:');
        console.log('1. git add . (파일 스테이징)');
        console.log('2. git commit -m "Initial commit" (커밋)');
        console.log('3. git push -u origin main (첫 푸시)');
        
        return {
            success: true,
            remoteUrl: GITHUB_CONFIG.httpsUrl,
            branch: runGitCommand('git branch --show-current', '') || 'main'
        };
        
    } catch (error) {
        console.error('\n💥 오류 발생:', error.message);
        console.error('\n🔧 문제 해결 방법:');
        console.error('1. Git이 설치되어 있는지 확인');
        console.error('2. 현재 디렉토리가 Git 저장소인지 확인');
        console.error('3. GitHub 저장소가 생성되었는지 확인');
        console.error('4. 네트워크 연결 상태 확인');
        console.error('5. GitHub 접근 권한 확인');
        
        return {
            success: false,
            error: error.message
        };
    }
}

// 스크립트 직접 실행 시
if (require.main === module) {
    setupGitRemote();
}

module.exports = {
    setupGitRemote,
    GITHUB_CONFIG
};
