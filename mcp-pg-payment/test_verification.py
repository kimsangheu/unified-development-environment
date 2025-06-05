"""
2단계 검증 스크립트
프로젝트가 정상적으로 작동하는지 확인하는 스크립트
"""
import sys
import traceback
from pathlib import Path

def test_imports():
    """모듈 import 테스트"""
    print("🔍 모듈 import 테스트 시작...")
    
    try:
        # 1단계: 데이터 모델 테스트
        from src.mcp_server.models.enums import PGProvider, PaymentStatus, PaymentMethod
        from src.mcp_server.models.base import Payment, Transaction, Cancel
        from src.mcp_server.models.exceptions import PaymentException
        print("✅ 1단계: 데이터 모델 import 성공")
        
        # 2단계: PG 클라이언트 구조 테스트
        from src.mcp_server.config import Config, PGConfig, Environment
        from src.mcp_server.pg_handlers.base import BasePGClient
        from src.mcp_server.pg_handlers.factory import PGClientFactory, PGClientManager
        from src.mcp_server.pg_handlers.exceptions import PGClientException
        from src.mcp_server.pg_handlers.monitoring import PGMetricsCollector
        print("✅ 2단계: PG 클라이언트 구조 import 성공")
        
        return True
        
    except Exception as e:
        print(f"❌ Import 실패: {e}")
        traceback.print_exc()
        return False

def test_basic_functionality():
    """기본 기능 테스트"""
    print("\n🔍 기본 기능 테스트 시작...")
    
    try:
        from src.mcp_server.models.enums import PGProvider
        from src.mcp_server.config import Config, PGConfig, Environment
        from src.mcp_server.pg_handlers.factory import PGClientFactory
        
        # 설정 생성 테스트
        config = Config(Environment.DEVELOPMENT)
        print("✅ Config 인스턴스 생성 성공")
        
        # PG 설정 추가 테스트
        test_config = PGConfig(
            merchant_id="test_merchant",
            api_key="test_api_key",
            api_base_url="https://api.test.com"
        )
        # KG이니시스 설정 추가 테스트
        kg_config = PGConfig(
            merchant_id="INIpayTest",
            api_key="not_used",
            secret_key="ItEQKi3rY7uvDS8l",
            api_base_url="https://iniapi.inicis.com",
            extra_config={'iv': '7uvDS8l_YESYh2x'}
        )
        config.add_pg_config(PGProvider.KG_INICIS, kg_config)
        print("✅ PG 설정 추가 성공")
        
        # 팩토리 생성 테스트
        factory = PGClientFactory(config)
        print("✅ PGClientFactory 생성 성공")
        
        # 사용 가능한 PG사 확인
        available = factory.get_available_providers()
        print(f"✅ 사용 가능한 PG사 확인: {len(available)}개 - {[p.value for p in available]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 기본 기능 테스트 실패: {e}")
        traceback.print_exc()
        return False

def test_data_models():
    """데이터 모델 생성 테스트"""
    print("\n🔍 데이터 모델 생성 테스트 시작...")
    
    try:
        from src.mcp_server.models.base import Payment
        from src.mcp_server.models.enums import PGProvider, PaymentStatus, PaymentMethod
        
        # Payment 모델 생성 테스트
        payment = Payment(
            payment_key="test_payment_key",
            order_id="ORDER_123",
            amount="10000",
            status=PaymentStatus.READY,
            method=PaymentMethod.CARD,
            provider=PGProvider.KG_INICIS
        )
        print("✅ Payment 모델 생성 성공")
        print(f"   - payment_key: {payment.payment_key}")
        print(f"   - amount: {payment.amount}")
        print(f"   - status: {payment.status.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 데이터 모델 테스트 실패: {e}")
        traceback.print_exc()
        return False

def test_monitoring():
    """모니터링 시스템 테스트"""
    print("\n🔍 모니터링 시스템 테스트 시작...")
    
    try:
        from src.mcp_server.pg_handlers.monitoring import PGMetricsCollector
        from src.mcp_server.models.enums import PGProvider
        
        # 메트릭 수집기 생성
        collector = PGMetricsCollector()
        print("✅ PGMetricsCollector 생성 성공")
        
        # 가상 메트릭 기록
        collector.record_request(
            provider=PGProvider.KG_INICIS,
            endpoint="/payments",
            method="POST",
            status_code=200,
            response_time=150.0,
            success=True
        )
        print("✅ 메트릭 기록 성공")
        
        # 메트릭 조회
        metrics = collector.get_metrics(PGProvider.KG_INICIS)
        print(f"✅ 메트릭 조회 성공: {metrics['total_requests']}개 요청")
        
        return True
        
    except Exception as e:
        print(f"❌ 모니터링 테스트 실패: {e}")
        traceback.print_exc()
        return False

def check_file_structure():
    """파일 구조 검증"""
    print("\n🔍 파일 구조 검증 시작...")
    
    required_files = [
        "src/mcp_server/__init__.py",
        "src/mcp_server/models/__init__.py",
        "src/mcp_server/models/base.py",
        "src/mcp_server/models/enums.py",
        "src/mcp_server/models/exceptions.py",
        "src/mcp_server/config.py",
        "src/mcp_server/pg_handlers/__init__.py",
        "src/mcp_server/pg_handlers/base.py",
        "src/mcp_server/pg_handlers/exceptions.py",
        "src/mcp_server/pg_handlers/factory.py",
        "src/mcp_server/pg_handlers/monitoring.py",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ 누락된 파일들: {missing_files}")
        return False
    else:
        print(f"✅ 모든 필수 파일 존재 확인: {len(required_files)}개")
        return True

def main():
    """메인 검증 실행"""
    print("🚀 2단계 프로젝트 검증 시작")
    print("=" * 50)
    
    # 현재 작업 디렉토리 확인
    current_dir = Path.cwd()
    print(f"📂 현재 디렉토리: {current_dir}")
    
    # 파이썬 경로에 프로젝트 루트 추가
    project_root = current_dir
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    tests = [
        ("파일 구조", check_file_structure),
        ("모듈 Import", test_imports),
        ("기본 기능", test_basic_functionality),
        ("데이터 모델", test_data_models),
        ("모니터링", test_monitoring),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 테스트 중 예외 발생: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 검증 결과 요약")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n🎯 전체 결과: {passed}/{total} 테스트 통과 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 모든 테스트 통과! 프로젝트가 정상 작동합니다.")
    else:
        print("⚠️ 일부 테스트 실패. 문제를 확인해주세요.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
