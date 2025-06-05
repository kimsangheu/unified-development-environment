"""
PG 클라이언트 사용 예제 및 테스트
"""
import asyncio
import os
from typing import Dict, Any

from ..models.enums import PGProvider
from ..config import Config, PGConfig, Environment
from .factory import PGClientFactory, PGClientManager
from .monitoring import setup_pg_logging


class ExamplePGClient:
    """예제용 PG 클라이언트 (실제 구현 시 BasePGClient 상속)"""
    
    def __init__(self, config: PGConfig, provider: PGProvider):
        self.config = config
        self.provider = provider
    
    def _get_auth_headers(self, **kwargs) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.config.api_key}"}
    
    async def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "success", "payment_key": "test_payment_key"}
    
    async def confirm_payment(self, payment_key: str, order_id: str, amount: str) -> Dict[str, Any]:
        return {"status": "confirmed"}
    
    async def get_payment(self, payment_key: str) -> Dict[str, Any]:
        return {"status": "success", "payment_key": payment_key}
    
    async def cancel_payment(self, payment_key: str, cancel_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "cancelled"}
    
    async def verify_webhook(self, payload: str, signature: str) -> bool:
        return True
    
    async def close(self):
        pass


async def example_basic_usage():
    """기본 사용법 예제"""
    print("=== PG 클라이언트 기본 사용법 ===")
    
    # 로깅 설정
    setup_pg_logging()
    
    # 설정 생성
    config = Config(Environment.DEVELOPMENT)
    
    # 테스트용 PG 설정 추가
    test_config = PGConfig(
        merchant_id="test_merchant",
        api_key="test_api_key",
        secret_key="test_secret",
        api_base_url="https://api.test.com",
        is_production=False
    )
    config.add_pg_config(PGProvider.KG_INICIS, test_config)
    
    # 팩토리 생성 및 클라이언트 등록
    factory = PGClientFactory(config)
    factory.register_client(PGProvider.KG_INICIS, ExamplePGClient)
    
    # 클라이언트 생성
    try:
        client = factory.create_client(PGProvider.KG_INICIS)
        print(f"클라이언트 생성 성공: {client.provider.value}")
        
        # 결제 생성 예제
        payment_result = await client.create_payment({
            "order_id": "ORDER_123",
            "amount": "10000",
            "order_name": "테스트 상품"
        })
        print(f"결제 생성 결과: {payment_result}")
        
        # 결제 조회 예제
        payment_info = await client.get_payment("test_payment_key")
        print(f"결제 조회 결과: {payment_info}")
        
        await client.close()
        
    except Exception as e:
        print(f"오류 발생: {e}")


async def example_manager_usage():
    """매니저 사용법 예제"""
    print("\n=== PG 클라이언트 매니저 사용법 ===")
    
    # 설정 준비
    config = Config(Environment.DEVELOPMENT)
    test_config = PGConfig(
        merchant_id="test_merchant",
        api_key="test_api_key",
        api_base_url="https://api.test.com"
    )
    config.add_pg_config(PGProvider.KG_INICIS, test_config)
    
    # 팩토리 및 매니저 설정
    factory = PGClientFactory(config)
    factory.register_client(PGProvider.KG_INICIS, ExamplePGClient)
    
    manager = PGClientManager(factory)
    
    try:
        # 사용 가능한 클라이언트 가져오기
        client = await manager.get_best_available_client()
        print(f"사용 가능한 클라이언트: {client.provider.value}")
        
        # 폴백 로직으로 작업 실행
        async def payment_operation(client, order_id):
            return await client.create_payment({"order_id": order_id})
        
        result = await manager.execute_with_fallback(
            payment_operation,
            providers=[PGProvider.KG_INICIS],
            order_id="ORDER_456"
        )
        print(f"폴백 실행 결과: {result}")
        
        # 상태 확인
        status = manager.get_status()
        print(f"PG사 상태: {status}")
        
        await manager.close_all()
        
    except Exception as e:
        print(f"오류 발생: {e}")


async def example_monitoring():
    """모니터링 기능 예제"""
    print("\n=== 모니터링 기능 예제 ===")
    
    from .monitoring import get_metrics_collector
    
    # 메트릭 수집기 가져오기
    collector = get_metrics_collector()
    
    # 가상의 요청 메트릭 기록
    collector.record_request(
        provider=PGProvider.KG_INICIS,
        endpoint="/payments",
        method="POST",
        status_code=200,
        response_time=150.5,
        success=True
    )
    
    collector.record_request(
        provider=PGProvider.KG_INICIS,
        endpoint="/payments",
        method="POST",
        status_code=500,
        response_time=300.0,
        success=False,
        error_type="PGHttpException",
        error_message="Internal Server Error"
    )
    
    # 메트릭 조회
    metrics = collector.get_metrics(PGProvider.KG_INICIS)
    print(f"KG이니시스 메트릭: {metrics}")
    
    # 전체 메트릭 조회
    all_metrics = collector.get_metrics()
    print(f"전체 메트릭: {all_metrics}")
    
    # 헬스 체크
    health = collector.get_health_status()
    print(f"헬스 상태: {health}")


async def example_environment_config():
    """환경별 설정 예제"""
    print("\n=== 환경별 설정 예제 ===")
    
    # 환경변수 설정 시뮬레이션
    os.environ.update({
        "KG_INICIS_MERCHANT_ID": "INIpayTest",
        "KG_INICIS_API_KEY": "test_api_key_123",
        "KG_INICIS_SECRET_KEY": "test_secret_key_456",
        "KG_INICIS_TIMEOUT": "60",
        "KG_INICIS_MAX_RETRIES": "5",
        "ENVIRONMENT": "development"
    })
    
    # 설정 로드
    config = Config()
    
    # 설정된 PG사 확인
    configured_providers = config.get_configured_providers()
    print(f"설정된 PG사: {[p.value for p in configured_providers]}")
    
    # 특정 PG사 설정 확인
    kg_inicis_config = config.get_pg_config(PGProvider.KG_INICIS)
    if kg_inicis_config:
        print(f"KG이니시스 설정: merchant_id={kg_inicis_config.merchant_id}, timeout={kg_inicis_config.timeout}")
    
    # 환경 정보
    print(f"현재 환경: {config.env.value}")
    print(f"운영 환경 여부: {config.is_production}")


async def main():
    """메인 예제 실행 함수"""
    try:
        await example_basic_usage()
        await example_manager_usage()
        await example_monitoring()
        await example_environment_config()
        
    except Exception as e:
        print(f"예제 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 예제 실행
    asyncio.run(main())
