const fs = require('fs');
const path = require('path');

console.log('🔍 Git 저장소 초기화 검증 시작...\n');

let allChecks = true;

// 1. .gitignore 파일 존재 확인
const gitignoreExists = fs.existsSync('.gitignore');
console.log(`📝 .gitignore 파일: ${gitignoreExists ? '✅ 존재' : '❌ 없음'}`);
if (!gitignoreExists) allChecks = false;

// 2. README.md 파일 존재 확인
const readmeExists = fs.existsSync('README.md');
console.log(`📝 README.md 파일: ${readmeExists ? '✅ 존재' : '❌ 없음'}`);
if (!readmeExists) allChecks = false;

// 3. package.json 업데이트 확인
try {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    const hasName = packageJson.name === 'kg-inicis-pg-integration';
    const hasScripts = packageJson.scripts && packageJson.scripts['init-git'];
    
    console.log(`📦 package.json 이름: ${hasName ? '✅ 설정됨' : '❌ 미설정'}`);
    console.log(`🚀 init-git 스크립트: ${hasScripts ? '✅ 설정됨' : '❌ 미설정'}`);
    
    if (!hasName || !hasScripts) allChecks = false;
} catch (error) {
    console.log('❌ package.json 읽기 오류:', error.message);
    allChecks = false;
}

// 4. .gitignore 내용 검증
if (gitignoreExists) {
    try {
        const gitignoreContent = fs.readFileSync('.gitignore', 'utf8');
        const requiredPatterns = [
            'node_modules/',
            '*.log',
            '.env',
            '*.key',
            '*.pem'
        ];
        
        let patternsFound = 0;
        requiredPatterns.forEach(pattern => {
            if (gitignoreContent.includes(pattern)) {
                patternsFound++;
            }
        });
        
        const allPatternsFound = patternsFound === requiredPatterns.length;
        console.log(`🔒 .gitignore 보안 패턴: ${allPatternsFound ? '✅ 모두 포함' : `❌ ${patternsFound}/${requiredPatterns.length} 패턴만 포함`}`);
        
        if (!allPatternsFound) allChecks = false;
    } catch (error) {
        console.log('❌ .gitignore 읽기 오류:', error.message);
        allChecks = false;
    }
}

// 5. 민감 파일 추적 여부 확인 (시뮬레이션)
const sensitiveFiles = [
    'node_modules',
    '.env',
    'config.key',
    'private.pem'
];

console.log('\n🔍 민감 파일 추적 상태 확인:');
sensitiveFiles.forEach(file => {
    const exists = fs.existsSync(file);
    if (exists) {
        console.log(`⚠️  ${file}: 존재함 (Git에서 제외되어야 함)`);
    } else {
        console.log(`✅ ${file}: 존재하지 않음`);
    }
});

// 6. 프로젝트 파일 구조 확인
const requiredFiles = [
    'app.js',
    'properties.js',
    'views/INIstdpay_pc_req.html',
    'views/INIstdpay_pc_return.ejs',
    'shrimp-rules.md'
];

console.log('\n📁 프로젝트 파일 구조 확인:');
let fileStructureOk = true;
requiredFiles.forEach(file => {
    const exists = fs.existsSync(file);
    console.log(`${exists ? '✅' : '❌'} ${file}`);
    if (!exists) fileStructureOk = false;
});

if (!fileStructureOk) allChecks = false;

// 최종 결과
console.log('\n' + '='.repeat(50));
if (allChecks) {
    console.log('🎉 Git 저장소 초기화 검증 완료!');
    console.log('✅ 모든 검사 항목이 통과되었습니다.');
    console.log('\n📋 다음 단계:');
    console.log('   1. npm run init-git 실행 (실제 Git 초기화)');
    console.log('   2. git status로 상태 확인');
    console.log('   3. 다음 작업 단계 진행');
} else {
    console.log('❌ Git 저장소 초기화 검증 실패!');
    console.log('⚠️  위의 실패 항목들을 수정해주세요.');
    process.exit(1);
}
