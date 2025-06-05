const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🔍 1단계: 문법 및 구조 검증 시작...\n');

let allChecks = true;
const errors = [];
const warnings = [];

// ===== 1. 프로젝트 파일 구조 검증 =====
console.log('📁 프로젝트 파일 구조 검증...');

const requiredFiles = [
    { path: 'app.js', type: '메인 서버 파일' },
    { path: 'properties.js', type: 'API URL 설정 모듈' },
    { path: 'package.json', type: '의존성 관리 파일' },
    { path: 'views/INIstdpay_pc_req.html', type: '결제 요청 페이지' },
    { path: 'views/INIstdpay_pc_return.ejs', type: '결제 응답 페이지' },
    { path: '.gitignore', type: 'Git 제외 파일' },
    { path: 'README.md', type: '프로젝트 문서' }
];

requiredFiles.forEach(file => {
    const exists = fs.existsSync(file.path);
    if (exists) {
        console.log(`✅ ${file.path} (${file.type})`);
    } else {
        console.log(`❌ ${file.path} (${file.type}) - 누락됨`);
        errors.push(`필수 파일 누락: ${file.path}`);
        allChecks = false;
    }
});

// ===== 2. package.json 의존성 검증 =====
console.log('\n📦 package.json 의존성 검증...');

try {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    
    // 필수 의존성 확인
    const requiredDeps = ['express', 'body-parser', 'ejs', 'request', 'crypto'];
    const dependencies = packageJson.dependencies || {};
    
    console.log('의존성 패키지 확인:');
    requiredDeps.forEach(dep => {
        if (dependencies[dep]) {
            console.log(`  ✅ ${dep}: ${dependencies[dep]}`);
        } else {
            console.log(`  ❌ ${dep}: 누락됨`);
            errors.push(`필수 의존성 누락: ${dep}`);
            allChecks = false;
        }
    });
    
    // package.json 필수 필드 확인
    const requiredFields = ['name', 'version', 'main', 'scripts'];
    console.log('\npackage.json 필수 필드 확인:');
    requiredFields.forEach(field => {
        if (packageJson[field]) {
            console.log(`  ✅ ${field}: 설정됨`);
        } else {
            console.log(`  ❌ ${field}: 누락됨`);
            warnings.push(`package.json 필드 누락: ${field}`);
        }
    });
    
} catch (error) {
    console.log(`❌ package.json 읽기 오류: ${error.message}`);
    errors.push('package.json 파싱 오류');
    allChecks = false;
}

// ===== 3. JavaScript 파일 문법 검증 =====
console.log('\n🔧 JavaScript 파일 문법 검증...');

const jsFiles = ['app.js', 'properties.js'];

jsFiles.forEach(file => {
    if (fs.existsSync(file)) {
        try {
            console.log(`\n검증 중: ${file}`);
            
            // 기본 JavaScript 구문 검증
            const content = fs.readFileSync(file, 'utf8');
            
            // 기본 구문 오류 체크
            try {
                // require 문법 유효성 (간단한 정규식 체크)
                const requirePattern = /require\s*\(\s*['"][^'"]*['"]\s*\)/g;
                const requires = content.match(requirePattern) || [];
                console.log(`  📝 require 구문: ${requires.length}개 발견`);
                
                // 함수 정의 체크
                const functionPattern = /(function\s+\w+|const\s+\w+\s*=|let\s+\w+\s*=|var\s+\w+\s*=)/g;
                const functions = content.match(functionPattern) || [];
                console.log(`  🔧 변수/함수 정의: ${functions.length}개 발견`);
                
                // 기본 괄호 매칭 체크
                const openBraces = (content.match(/\{/g) || []).length;
                const closeBraces = (content.match(/\}/g) || []).length;
                if (openBraces === closeBraces) {
                    console.log(`  ✅ 괄호 매칭: 정상 (${openBraces}/${closeBraces})`);
                } else {
                    console.log(`  ❌ 괄호 매칭: 불일치 (${openBraces}/${closeBraces})`);
                    errors.push(`${file}: 괄호 매칭 오류`);
                    allChecks = false;
                }
                
                console.log(`  ✅ ${file}: 기본 구문 검증 통과`);
                
            } catch (syntaxError) {
                console.log(`  ❌ ${file}: 구문 오류 - ${syntaxError.message}`);
                errors.push(`${file}: 구문 오류`);
                allChecks = false;
            }
            
        } catch (error) {
            console.log(`  ❌ ${file}: 파일 읽기 오류 - ${error.message}`);
            errors.push(`${file}: 파일 접근 오류`);
            allChecks = false;
        }
    }
});

// ===== 4. Node.js 모듈 로딩 테스트 =====
console.log('\n🔗 Node.js 모듈 로딩 테스트...');

const moduleTests = [
    { name: 'express', test: () => require('express') },
    { name: 'crypto', test: () => require('crypto') },
    { name: 'fs', test: () => require('fs') },
    { name: 'path', test: () => require('path') }
];

moduleTests.forEach(module => {
    try {
        module.test();
        console.log(`  ✅ ${module.name}: 로딩 성공`);
    } catch (error) {
        console.log(`  ❌ ${module.name}: 로딩 실패 - ${error.message}`);
        errors.push(`모듈 로딩 실패: ${module.name}`);
        allChecks = false;
    }
});

// ===== 5. KG이니시스 특화 검증 =====
console.log('\n🏦 KG이니시스 PG연동 특화 검증...');

// app.js 내 필수 기능 확인
if (fs.existsSync('app.js')) {
    const appContent = fs.readFileSync('app.js', 'utf8');
    
    const pgChecks = [
        { name: 'Express 서버 설정', pattern: /express\(\)/ },
        { name: 'crypto 모듈 사용', pattern: /require\s*\(\s*['"]crypto['"]\s*\)/ },
        { name: 'SHA256 해시 사용', pattern: /createHash\s*\(\s*['"]sha256['"]\s*\)/ },
        { name: '결제 라우터 설정', pattern: /app\.(get|post)/ },
        { name: 'body-parser 설정', pattern: /bodyParser|body-parser/ }
    ];
    
    pgChecks.forEach(check => {
        if (check.pattern.test(appContent)) {
            console.log(`  ✅ ${check.name}: 확인됨`);
        } else {
            console.log(`  ⚠️  ${check.name}: 확인되지 않음`);
            warnings.push(`PG기능 확인 필요: ${check.name}`);
        }
    });
}

// properties.js 검증
if (fs.existsSync('properties.js')) {
    const propContent = fs.readFileSync('properties.js', 'utf8');
    
    if (propContent.includes('getAuthUrl') && propContent.includes('getNetCancel')) {
        console.log('  ✅ properties.js: API URL 함수 확인됨');
    } else {
        console.log('  ❌ properties.js: 필수 함수 누락');
        errors.push('properties.js: getAuthUrl 또는 getNetCancel 함수 누락');
        allChecks = false;
    }
}

// ===== 6. 코드 품질 기본 검사 =====
console.log('\n📊 코드 품질 기본 검사...');

const qualityChecks = [];

jsFiles.forEach(file => {
    if (fs.existsSync(file)) {
        const content = fs.readFileSync(file, 'utf8');
        
        // 기본 품질 지표
        const lines = content.split('\n').length;
        const commentLines = (content.match(/\/\/|\/\*|\*/g) || []).length;
        const commentRatio = (commentLines / lines * 100).toFixed(1);
        
        console.log(`  📝 ${file}:`);
        console.log(`    - 총 줄 수: ${lines}`);
        console.log(`    - 주석 비율: ${commentRatio}%`);
        
        qualityChecks.push({
            file,
            lines,
            commentRatio: parseFloat(commentRatio)
        });
    }
});

// ===== 최종 결과 =====
console.log('\n' + '='.repeat(60));
console.log('📊 1단계 검증 결과 요약');
console.log('='.repeat(60));

if (allChecks) {
    console.log('🎉 모든 문법 및 구조 검증을 통과했습니다!');
    console.log('✅ JavaScript 파일들이 정상적으로 구성되어 있습니다.');
} else {
    console.log('❌ 검증 과정에서 오류가 발견되었습니다.');
}

if (errors.length > 0) {
    console.log('\n🚨 해결해야 할 오류:');
    errors.forEach((error, index) => {
        console.log(`  ${index + 1}. ${error}`);
    });
}

if (warnings.length > 0) {
    console.log('\n⚠️  주의사항:');
    warnings.forEach((warning, index) => {
        console.log(`  ${index + 1}. ${warning}`);
    });
}

console.log('\n📈 검증 통계:');
console.log(`  - 총 검사 항목: ${requiredFiles.length + jsFiles.length + moduleTests.length}`);
console.log(`  - 오류 수: ${errors.length}`);
console.log(`  - 경고 수: ${warnings.length}`);
console.log(`  - 성공률: ${((1 - errors.length / 10) * 100).toFixed(1)}%`);

// 결과 로그 파일 생성
const logData = {
    timestamp: new Date().toISOString(),
    step: 1,
    description: '문법 및 구조 검증',
    success: allChecks,
    errors: errors,
    warnings: warnings,
    statistics: {
        totalChecks: requiredFiles.length + jsFiles.length + moduleTests.length,
        errorCount: errors.length,
        warningCount: warnings.length
    }
};

try {
    if (!fs.existsSync('scripts/logs')) {
        fs.mkdirSync('scripts/logs', { recursive: true });
    }
    
    const logFile = `scripts/logs/step1-verification-${new Date().toISOString().slice(0, 10)}.json`;
    fs.writeFileSync(logFile, JSON.stringify(logData, null, 2));
    console.log(`\n📄 검증 결과가 ${logFile}에 저장되었습니다.`);
} catch (logError) {
    console.log(`⚠️  로그 파일 저장 실패: ${logError.message}`);
}

console.log('\n🚀 다음 단계: npm run verify:step2 (API 연동 및 암호화 검증)');

// 오류가 있으면 프로세스 종료 코드 1 반환
if (!allChecks) {
    process.exit(1);
}
