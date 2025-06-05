const { execSync } = require('child_process');
const fs = require('fs');

console.log('🧪 1단계 검증 스크립트 테스트 실행...\n');

try {
    // 1. scripts 디렉토리 확인
    if (!fs.existsSync('scripts')) {
        console.log('❌ scripts 디렉토리가 존재하지 않습니다.');
        process.exit(1);
    }
    console.log('✅ scripts 디렉토리 확인됨');
    
    // 2. step1-syntax.js 파일 확인
    if (!fs.existsSync('scripts/step1-syntax.js')) {
        console.log('❌ step1-syntax.js 파일이 존재하지 않습니다.');
        process.exit(1);
    }
    console.log('✅ step1-syntax.js 파일 확인됨');
    
    // 3. .eslintrc.js 파일 확인
    if (!fs.existsSync('.eslintrc.js')) {
        console.log('❌ .eslintrc.js 파일이 존재하지 않습니다.');
        process.exit(1);
    }
    console.log('✅ .eslintrc.js 파일 확인됨');
    
    // 4. package.json scripts 확인
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    if (!packageJson.scripts || !packageJson.scripts['verify:step1']) {
        console.log('❌ package.json에 verify:step1 스크립트가 없습니다.');
        process.exit(1);
    }
    console.log('✅ package.json verify:step1 스크립트 확인됨');
    
    // 5. 기본 Node.js 구문 검증 테스트
    console.log('\n🔧 기본 Node.js 환경 테스트...');
    
    const testModules = ['fs', 'path', 'child_process'];
    testModules.forEach(module => {
        try {
            require(module);
            console.log(`✅ ${module} 모듈 로딩 성공`);
        } catch (error) {
            console.log(`❌ ${module} 모듈 로딩 실패: ${error.message}`);
            process.exit(1);
        }
    });
    
    console.log('\n🎉 1단계 검증 스크립트 준비가 완료되었습니다!');
    console.log('\n🚀 실행 명령어:');
    console.log('   npm run verify:step1    # 1단계 검증 실행');
    console.log('   npm run verify          # 전체 검증 실행 (현재는 1단계만)');
    
    console.log('\n📋 검증 항목:');
    console.log('   ✓ 프로젝트 파일 구조');
    console.log('   ✓ package.json 의존성');
    console.log('   ✓ JavaScript 파일 문법');
    console.log('   ✓ Node.js 모듈 로딩');
    console.log('   ✓ KG이니시스 PG연동 특화 검증');
    console.log('   ✓ 코드 품질 기본 검사');
    
} catch (error) {
    console.error('❌ 테스트 실행 중 오류 발생:', error.message);
    process.exit(1);
}
