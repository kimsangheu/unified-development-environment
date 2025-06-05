#!/usr/bin/env node

const { execSync } = require('child_process');
const path = require('path');

console.log('🔧 Git 소유권 문제 해결');
console.log('================================\n');

// 현재 디렉토리 경로
const currentPath = process.cwd();
console.log(`📁 현재 디렉토리: ${currentPath}\n`);

try {
    console.log('🔍 1. Git safe.directory 설정 추가...');
    
    // Windows 경로를 Git에서 인식할 수 있는 형태로 변환
    const gitPath = currentPath.replace(/\\/g, '/');
    console.log(`   설정할 경로: ${gitPath}`);
    
    // safe.directory 추가
    const command = `git config --global --add safe.directory "${gitPath}"`;
    console.log(`   실행 명령: ${command}`);
    
    execSync(command, { stdio: 'inherit' });
    console.log('✅ safe.directory 설정 완료\n');
    
    console.log('🔍 2. Git 상태 재확인...');
    try {
        const status = execSync('git status --porcelain', { encoding: 'utf8' });
        console.log('✅ Git 상태 확인 성공');
        
        if (status.trim()) {
            console.log('📝 변경된 파일들:');
            console.log(status);
        } else {
            console.log('📝 변경사항 없음');
        }
    } catch (error) {
        console.log('❌ Git 상태 확인 여전히 실패:', error.message);
    }
    
    console.log('\n🔍 3. 원격 저장소 연결 재확인...');
    try {
        const remotes = execSync('git remote -v', { encoding: 'utf8' });
        console.log('✅ 원격 저장소 확인 성공:');
        console.log(remotes);
    } catch (error) {
        console.log('❌ 원격 저장소 확인 실패:', error.message);
    }
    
    console.log('\n🔍 4. 현재 브랜치 확인...');
    try {
        const branch = execSync('git branch --show-current', { encoding: 'utf8' }).trim();
        console.log(`✅ 현재 브랜치: ${branch}`);
    } catch (error) {
        console.log('❌ 브랜치 확인 실패:', error.message);
    }
    
    console.log('\n🎯 문제 해결 완료!');
    console.log('이제 다음 명령으로 Git 연결을 다시 확인해보세요:');
    console.log('node scripts/verify-git-connection.js');
    
} catch (error) {
    console.error('❌ 오류 발생:', error.message);
    console.log('\n💡 대안 해결방법:');
    console.log('1. PowerShell을 관리자 권한으로 실행');
    console.log('2. 다음 명령 실행:');
    console.log(`   git config --global --add safe.directory "${currentPath.replace(/\\/g, '/')}"`);
}
