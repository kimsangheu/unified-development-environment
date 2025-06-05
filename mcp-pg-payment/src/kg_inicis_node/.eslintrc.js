module.exports = {
    "env": {
        "browser": true,
        "commonjs": true,
        "es6": true,
        "node": true
    },
    "extends": "eslint:recommended",
    "parserOptions": {
        "ecmaVersion": 2018
    },
    "rules": {
        // 기존 코드와 호환되도록 엄격하지 않은 설정
        "indent": ["warn", 4, { "SwitchCase": 1 }],
        "linebreak-style": "off", // Windows/Unix 줄바꿈 호환
        "quotes": ["warn", "double", { "allowTemplateLiterals": true }],
        "semi": ["error", "always"],
        "no-unused-vars": ["warn"],
        "no-console": "off", // console.log 허용
        "no-undef": "error",
        "no-redeclare": "error",
        "no-unreachable": "error",
        "valid-typeof": "error",
        "no-irregular-whitespace": "warn",
        "no-trailing-spaces": "warn"
    },
    "globals": {
        // 전역 변수 허용
        "process": "readonly",
        "Buffer": "readonly",
        "__dirname": "readonly",
        "__filename": "readonly"
    }
};
