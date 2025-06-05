"""
통합 결제 시스템 데모

PaymentService와 PaymentAPI의 사용 예제를 제공합니다.
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from ..services import (
    PaymentAPI,
    PaymentServiceMode,
    create_payment_api,
    create_single_provider_api,
    create_multi_provider_api
)
from ..models.requests import PaymentRequest, PaymentStatusRequest, PaymentCancelRequest
from ..models.base import CustomerInfo
from ..models.enums import PGProvider, PaymentMethod
from ..models.exceptions import PaymentException


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PaymentDemo:
    """결제 시스템 데모 클래스"""
    
    def __init__(self):
        self.payment_api: Optional[PaymentAPI] = None
    
    async def setup(self, mode: PaymentServiceMode = PaymentServiceMode.MULTI):
        """데모 환경 설정"""
        logger.info(f"결제 시스템 데모 초기화 - 모드: {mode}")
        
        if mode == PaymentServiceMode.SINGLE:
            # 단일 PG사 모드 (KG이니시스)
            self.payment_api = create_single_provider_api(PGProvider.KG_INICIS)
        elif mode == PaymentServiceMode.MULTI:
            # 다중 PG사 폴백 모드
            self.payment_api = create_multi_provider_api(
                primary=PGProvider.KG_INICIS,
                fallbacks=[PGProvider.TOSS_PAYMENTS, PGProvider.NICE_PAYMENTS]
            )
        else:
            # 기본 다중 모드
            self.payment_api = create_payment_api(mode=mode)
        
        # 시스템 상태 확인
        health = await self.payment_api.health_check()
        logger.info(f"시스템 상태: {health['service']['status']}")
        
        # 지원하는 PG사 목록
        providers = self.payment_api.get_supported_providers()
        available_providers = [p for p in providers if p['available']]
        logger.info(f"사용 가능한 PG사: {[p['name'] for p in available_providers]}")
        
        return self.payment_api
    
    async def demo_basic_payment(self) -> bool:
        """기본 결제 데모"""
        logger.info("=== 기본 결제 데모 시작 ===")
        
        try:
            # 결제 요청 생성
            request = PaymentRequest(
                order_id=f"ORDER_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                amount=10000,
                currency="KRW",
                payment_method=PaymentMethod.CARD,
                product_name="데모 상품",
                customer_info=CustomerInfo(
                    name="홍길동",
                    email="demo@example.com",
                    phone="01012345678"
                ),
                return_url="https://example.com/return",
                cancel_url="https://example.com/cancel"
            )
            
            logger.info(f"결제 요청: 주문번호={request.order_id}, 금액={request.amount}")
            
            # 결제 처리
            response = await self.payment_api.process_payment(request)
            
            logger.info(f"결제 결과: 상태={response.status}, 메시지={response.message}")
            
            if response.status == "SUCCESS":
                logger.info("✅ 결제 성공!")
                return True
            else:
                logger.warning("⚠️ 결제 실패 또는 대기")
                return False
                
        except PaymentException as e:
            logger.error(f"❌ 결제 처리 실패: {str(e)}")
            return False
    
    async def demo_payment_status_check(self, order_id: str):
        """결제 상태 조회 데모"""
        logger.info("=== 결제 상태 조회 데모 ===")
        
        try:
            request = PaymentStatusRequest(order_id=order_id)
            response = await self.payment_api.get_payment_status(request)
            
            logger.info(f"결제 상태: {response.status}")
            logger.info(f"결제 금액: {response.amount}")
            logger.info(f"메시지: {response.message}")
            
        except PaymentException as e:
            logger.error(f"❌ 상태 조회 실패: {str(e)}")
    
    async def demo_payment_cancel(self, order_id: str):
        """결제 취소 데모"""
        logger.info("=== 결제 취소 데모 ===")
        
        try:
            request = PaymentCancelRequest(
                order_id=order_id,
                cancel_reason="고객 요청"
            )
            
            response = await self.payment_api.cancel_payment(request)
            
            logger.info(f"취소 결과: {response.status}")
            logger.info(f"취소 금액: {response.cancelled_amount}")
            logger.info(f"메시지: {response.message}")
            
        except PaymentException as e:
            logger.error(f"❌ 결제 취소 실패: {str(e)}")
    
    async def demo_batch_payments(self):
        """배치 결제 데모"""
        logger.info("=== 배치 결제 데모 시작 ===")
        
        # 여러 결제 요청 생성
        requests = []
        for i in range(3):
            request = PaymentRequest(
                order_id=f"BATCH_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i+1}",
                amount=1000 * (i + 1),  # 1000, 2000, 3000원
                currency="KRW",
                payment_method=PaymentMethod.CARD,
                product_name=f"배치 상품 {i+1}",
                customer_info=CustomerInfo(
                    name=f"고객{i+1}",
                    email=f"customer{i+1}@example.com",
                    phone=f"0101234567{i}"
                ),
                return_url="https://example.com/return",
                cancel_url="https://example.com/cancel"
            )
            requests.append(request)
        
        try:
            # 배치 결제 처리
            responses = await self.payment_api.batch_process_payments(
                requests=requests,
                max_concurrent=2
            )
            
            logger.info(f"배치 결제 완료: {len(responses)}건 처리")
            
            for i, response in enumerate(responses):
                logger.info(f"  {i+1}. {response.order_id}: {response.status}")
                
        except Exception as e:
            logger.error(f"❌ 배치 결제 실패: {str(e)}")
    
    async def demo_health_monitoring(self):
        """시스템 모니터링 데모"""
        logger.info("=== 시스템 모니터링 데모 ===")
        
        try:
            # 헬스체크
            health = await self.payment_api.health_check()
            
            logger.info("시스템 상태:")
            logger.info(f"  서비스: {health['service']['status']}")
            logger.info(f"  모드: {health['service']['mode']}")
            
            logger.info("PG사별 상태:")
            for provider, status in health['providers'].items():
                logger.info(f"  {provider}: {'✅' if status['available'] else '❌'}")
            
            # 서비스 정보
            info = self.payment_api.get_service_info()
            logger.info(f"API 버전: {info['api_version']}")
            logger.info(f"지원 PG사: {len(info['supported_providers'])}개")
            
        except Exception as e:
            logger.error(f"❌ 모니터링 실패: {str(e)}")
    
    async def demo_payment_history(self):
        """결제 이력 조회 데모"""
        logger.info("=== 결제 이력 조회 데모 ===")
        
        try:
            history = await self.payment_api.get_payment_history(limit=5)
            
            logger.info(f"최근 결제 이력: {len(history)}건")
            
            for item in history:
                logger.info(f"  주문번호: {item['order_id']}")
                logger.info(f"  상태: {item['status']}")
                logger.info(f"  시작: {item['started_at']}")
                logger.info(f"  완료: {item.get('completed_at', 'N/A')}")
                logger.info("  ---")
                
        except Exception as e:
            logger.error(f"❌ 이력 조회 실패: {str(e)}")
    
    async def cleanup(self):
        """리소스 정리"""
        if self.payment_api:
            await self.payment_api.close()
            logger.info("데모 종료 및 리소스 정리 완료")


async def run_full_demo():
    """전체 데모 실행"""
    demo = PaymentDemo()
    
    try:
        # 1. 시스템 초기화
        await demo.setup(PaymentServiceMode.MULTI)
        
        # 2. 시스템 모니터링
        await demo.demo_health_monitoring()
        
        # 3. 기본 결제 테스트
        success = await demo.demo_basic_payment()
        
        # 4. 배치 결제 테스트
        await demo.demo_batch_payments()
        
        # 5. 결제 이력 조회
        await demo.demo_payment_history()
        
        logger.info("🎉 전체 데모 완료!")
        
    except Exception as e:
        logger.error(f"❌ 데모 실행 실패: {str(e)}")
    
    finally:
        await demo.cleanup()


async def run_simple_payment_demo():
    """간단한 결제 데모"""
    logger.info("=== 간단한 결제 데모 ===")
    
    # KG이니시스만 사용하는 단순한 예제
    api = create_single_provider_api(PGProvider.KG_INICIS)
    
    try:
        # 결제 요청
        request = PaymentRequest(
            order_id=f"SIMPLE_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            amount=5000,
            currency="KRW",
            payment_method=PaymentMethod.CARD,
            product_name="간단한 테스트 상품",
            customer_info=CustomerInfo(
                name="테스트",
                email="test@example.com",
                phone="01000000000"
            ),
            return_url="https://example.com/return",
            cancel_url="https://example.com/cancel"
        )
        
        # 결제 처리
        response = await api.process_payment(request)
        
        logger.info(f"결제 결과: {response.status}")
        logger.info(f"주문번호: {response.order_id}")
        logger.info(f"메시지: {response.message}")
        
    except Exception as e:
        logger.error(f"결제 실패: {str(e)}")
    
    finally:
        await api.close()


def main():
    """메인 실행 함수"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "simple":
        # 간단한 데모 실행
        asyncio.run(run_simple_payment_demo())
    else:
        # 전체 데모 실행
        asyncio.run(run_full_demo())


if __name__ == "__main__":
    main()
