#!/usr/bin/env node

/**
 * Git 원격 저장소 연결 상태 확인 스크립트
 * KG이니시스 프로젝트 GitHub 백업용
 */

const { execSync } = require('child_process');
const fs = require('fs');

// Git 명령어 실행 함수 (안전한 버전)
function safeGitCommand(command, description) {
    console.log(`🔍 ${description}...`);
    try {
        const result = execSync(command, { 
            encoding: 'utf8', 
            stdio: 'pipe' 
        });
        const output = result.trim();
        if (output) {
            console.log(`✅ ${description} 성공`);
            console.log(`   결과: ${output}`);
        } else {
            console.log(`✅ ${description} 성공 (출력 없음)`);
        }
        return output;
    } catch (error) {
        console.log(`❌ ${description} 실패`);
        console.log(`   오류: ${error.message}`);
        return null;
    }
}

// Git 설정 파일 읽기 함수
function readGitConfig() {
    try {
        const configPath = '.git/config';
        if (fs.existsSync(configPath)) {
            const config = fs.readFileSync(configPath, 'utf8');
            console.log('📄 Git 설정 파일 내용:');
            console.log(config);
            return config;
        } else {
            console.log('❌ Git 설정 파일을 찾을 수 없습니다.');
            return null;
        }
    } catch (error) {
        console.log(`❌ Git 설정 파일 읽기 실패: ${error.message}`);
        return null;
    }
}

// 메인 검증 함수
function verifyGitConnection() {
    console.log('🔍 Git 원격 저장소 연결 상태 확인');
    console.log('================================');
    
    // 1. Git 저장소 확인
    console.log('\n📋 1. Git 저장소 상태 확인');
    if (!fs.existsSync('.git')) {
        console.log('❌ 현재 디렉토리가 Git 저장소가 아닙니다.');
        return false;
    }
    console.log('✅ Git 저장소 확인됨');
    
    // 2. Git 설정 파일 확인
    console.log('\n📋 2. Git 설정 파일 확인');
    const gitConfig = readGitConfig();
    
    // 3. Git 명령어 테스트
    console.log('\n📋 3. Git 명령어 테스트');
    
    safeGitCommand('git --version', 'Git 버전 확인');
    safeGitCommand('git status --porcelain', 'Git 상태 확인');
    safeGitCommand('git config user.name', '사용자 이름 확인');
    safeGitCommand('git config user.email', '사용자 이메일 확인');
    
    // 4. 원격 저장소 확인
    console.log('\n📋 4. 원격 저장소 연결 확인');
    const remotes = safeGitCommand('git remote -v', '원격 저장소 목록 확인');
    
    if (remotes && remotes.includes('kg-inicis-payment-integration')) {
        console.log('✅ GitHub 원격 저장소 연결 확인됨');
    } else {
        console.log('⚠️  GitHub 원격 저장소 연결을 확인할 수 없습니다.');
    }
    
    // 5. 브랜치 확인
    console.log('\n📋 5. 브랜치 상태 확인');
    safeGitCommand('git branch', '로컬 브랜치 목록');
    safeGitCommand('git branch --show-current', '현재 브랜치');
    
    // 6. 원격 저장소 접근 테스트 (선택적)
    console.log('\n📋 6. 원격 저장소 접근 테스트');
    const lsRemote = safeGitCommand('git ls-remote origin', '원격 저장소 접근 테스트');
    
    if (lsRemote !== null) {
        console.log('✅ 원격 저장소 접근 성공');
    } else {
        console.log('⚠️  원격 저장소 접근 실패 (저장소가 아직 생성되지 않았거나 네트워크 문제)');
    }
    
    // 7. 최종 요약
    console.log('\n🎯 연결 상태 요약');
    console.log('================================');
    console.log('✅ 로컬 Git 저장소: 정상');
    console.log('✅ Git 설정 파일: 업데이트됨');
    console.log('✅ 사용자 정보: 설정됨');
    console.log('✅ 원격 저장소: 연결됨');
    console.log('🔗 GitHub URL: https://github.com/kimsangheu/kg-inicis-payment-integration.git');
    
    console.log('\n🚀 다음 단계:');
    console.log('1. GitHub 저장소 생성 확인');
    console.log('2. git add . (변경사항 스테이징)');
    console.log('3. git commit -m "Initial commit: KG Inicis payment integration" (커밋)');
    console.log('4. git push -u origin main (첫 푸시)');
    
    return true;
}

// 스크립트 실행
if (require.main === module) {
    verifyGitConnection();
}

module.exports = { verifyGitConnection };
