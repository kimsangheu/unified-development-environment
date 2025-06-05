const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🚀 Git 저장소 초기화 시작...');

try {
    // 1. Git 저장소 초기화
    console.log('📁 Git 저장소 초기화 중...');
    execSync('git init', { stdio: 'inherit' });
    
    // 2. 기본 설정
    try {
        execSync('git config user.name "PG Developer"', { stdio: 'pipe' });
        execSync('git config user.email "developer@example.com"', { stdio: 'pipe' });
        console.log('✅ Git 사용자 설정 완료');
    } catch (e) {
        console.log('ℹ️  Git 전역 설정을 사용합니다.');
    }
    
    // 3. .gitignore 및 README.md 파일 존재 확인
    const gitignoreExists = fs.existsSync('.gitignore');
    const readmeExists = fs.existsSync('README.md');
    
    console.log(`📝 .gitignore 파일: ${gitignoreExists ? '✅ 존재' : '❌ 없음'}`);
    console.log(`📝 README.md 파일: ${readmeExists ? '✅ 존재' : '❌ 없음'}`);
    
    // 4. 초기 커밋 생성
    console.log('📦 파일 추가 및 초기 커밋 생성 중...');
    execSync('git add .', { stdio: 'inherit' });
    execSync('git commit -m "Initial commit: KG이니시스 PG연동 프로젝트 초기화"', { stdio: 'inherit' });
    
    // 5. main 브랜치명 설정 (기본 브랜치가 master인 경우 main으로 변경)
    try {
        execSync('git branch -M main', { stdio: 'pipe' });
        console.log('✅ 기본 브랜치를 main으로 설정');
    } catch (e) {
        console.log('ℹ️  브랜치 이름이 이미 main입니다.');
    }
    
    // 6. develop 브랜치 생성 및 체크아웃
    console.log('🌿 develop 브랜치 생성 중...');
    execSync('git checkout -b develop', { stdio: 'inherit' });
    
    // 7. Git 상태 확인
    console.log('\n📊 Git 저장소 상태:');
    execSync('git status', { stdio: 'inherit' });
    
    // 8. 브랜치 목록 확인
    console.log('\n🌳 생성된 브랜치 목록:');
    execSync('git branch -a', { stdio: 'inherit' });
    
    console.log('\n🎉 Git 저장소 초기화가 완료되었습니다!');
    console.log('\n📋 다음 단계:');
    console.log('   1. 기능 개발 시: git checkout -b feature/기능명');
    console.log('   2. 개발 완료 후: git checkout develop && git merge feature/기능명');
    console.log('   3. 운영 배포 시: git checkout main && git merge develop');
    
} catch (error) {
    console.error('❌ Git 저장소 초기화 중 오류 발생:', error.message);
    process.exit(1);
}
