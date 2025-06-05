"""
KG이니시스 클라이언트 사용 예제
"""
import asyncio
import os
from decimal import Decimal

from ...config import Config, PGConfig, Environment
from ...models.enums import PGProvider, PaymentMethod
from ..factory import PGClientFactory
from ..kg_inicis import KGInicisClient


async def kg_inicis_basic_example():
    """KG이니시스 기본 사용 예제"""
    print("\n=== KG이니시스 기본 사용 예제 ===")
    
    # 1. 설정 생성
    config = Config(Environment.DEVELOPMENT)
    
    # KG이니시스 설정 (테스트 환경)
    kg_config = PGConfig(
        merchant_id="INIpayTest",  # 테스트 상점 ID
        api_key="not_used_in_kg",  # KG이니시스는 사용하지 않음
        secret_key="ItEQKi3rY7uvDS8l",  # 테스트 INIAPI key
        api_base_url="https://iniapi.inicis.com",
        is_production=False,
        timeout=30,
        max_retries=3,
        extra_config={
            'iv': '7uvDS8l_YESYh2x'  # 테스트 IV
        }
    )
    
    config.add_pg_config(PGProvider.KG_INICIS, kg_config)
    
    # 2. 팩토리 생성 및 클라이언트 생성
    factory = PGClientFactory(config)
    client = factory.create_client(PGProvider.KG_INICIS)
    
    print(f"KG이니시스 클라이언트 생성 성공: {client.provider.value}")
    print(f"상점 ID: {client.merchant_id}")
    print(f"API 기본 URL: {client.api_base_url}")
    
    try:
        # 3. 결제 생성 예제 (결제창 방식)
        payment_data = {
            'order_id': 'TEST_ORDER_' + str(int(asyncio.get_event_loop().time())),
            'amount': 1000,
            'order_name': 'KG이니시스 테스트 상품',
            'buyer_name': '홍길동',
            'buyer_email': 'test@example.com',
            'buyer_tel': '010-1234-5678',
            'pay_method': 'Card'
        }
        
        print(f"\n결제 요청 데이터: {payment_data}")
        
        # 실제 결제 생성 (테스트 환경에서는 실제 API 호출하지 않음)
        # payment_result = await client.create_payment(payment_data)
        # print(f"결제 생성 결과: {payment_result}")
        
        # 모의 결제 결과
        mock_payment_key = "INIpayTest_20250604_TEST001"
        print(f"모의 결제 키: {mock_payment_key}")
        
        # 4. 결제 조회 예제
        print("\n=== 결제 조회 테스트 ===")
        # query_result = await client.get_payment(mock_payment_key)
        # print(f"결제 조회 결과: {query_result}")
        
        # 5. 결제 취소 예제
        print("\n=== 결제 취소 테스트 ===")
        cancel_data = {
            'reason': '테스트 취소',
            'cancel_amount': 1000
        }
        # cancel_result = await client.cancel_payment(mock_payment_key, cancel_data)
        # print(f"결제 취소 결과: {cancel_result}")
        
        print("\n✅ KG이니시스 기본 예제 완료 (실제 API 호출 없이 구조 테스트)")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    finally:
        await client.close()


async def kg_inicis_advanced_example():
    """KG이니시스 고급 기능 예제"""
    print("\n=== KG이니시스 고급 기능 예제 ===")
    
    # 환경변수 설정 시뮬레이션
    os.environ.update({
        "KG_INICIS_MERCHANT_ID": "INIpayTest",
        "KG_INICIS_SECRET_KEY": "ItEQKi3rY7uvDS8l",
        "KG_INICIS_IV": "7uvDS8l_YESYh2x",
        "ENVIRONMENT": "development"
    })
    
    # 설정 자동 로드
    config = Config(Environment.DEVELOPMENT)
    factory = PGClientFactory(config)
    
    # 사용 가능한 PG사 확인
    available = factory.get_available_providers()
    print(f"사용 가능한 PG사: {[p.value for p in available]}")
    
    if PGProvider.KG_INICIS in available:
        client = factory.create_client(PGProvider.KG_INICIS)
        
        # 1. 가상계좌 결제 예제
        print("\n=== 가상계좌 결제 예제 ===")
        va_payment_data = {
            'order_id': 'VA_ORDER_001',
            'amount': 50000,
            'order_name': '가상계좌 테스트 상품',
            'buyer_name': '김철수',
            'buyer_email': 'kimcs@example.com',
            'buyer_tel': '010-9876-5432',
            'pay_method': 'VCard',
            'va_due_date': '20251220'  # 입금 기한
        }
        
        print(f"가상계좌 결제 데이터: {va_payment_data}")
        
        # 2. 할부 카드 결제 예제
        print("\n=== 할부 카드 결제 예제 ===")
        card_payment_data = {
            'order_id': 'CARD_ORDER_001',
            'amount': 120000,
            'order_name': '할부 테스트 상품',
            'buyer_name': '이영희',
            'buyer_email': 'leeyh@example.com',
            'buyer_tel': '010-1111-2222',
            'pay_method': 'Card',
            'installment': 3  # 3개월 할부
        }
        
        print(f"할부 카드 결제 데이터: {card_payment_data}")
        
        # 3. 환불 계좌 정보가 있는 취소 예제
        print("\n=== 환불 계좌 취소 예제 ===")
        refund_cancel_data = {
            'reason': '고객 요청 환불',
            'cancel_amount': 50000,
            'refund_account': '1234567890',
            'refund_bank_code': '004',  # 국민은행
            'refund_holder_name': '김철수'
        }
        
        print(f"환불 취소 데이터: {refund_cancel_data}")
        
        # 4. AES 암호화 테스트
        print("\n=== AES 암호화 테스트 ===")
        test_account = "1234567890"
        encrypted_account = client._aes_encrypt(test_account)
        print(f"원본 계좌: {test_account}")
        print(f"암호화된 계좌: {encrypted_account}")
        
        # 5. 해시 생성 테스트
        print("\n=== 해시 생성 테스트 ===")
        test_params = {
            'type': 'cancel',
            'mid': 'INIpayTest',
            'tid': 'TEST_TID_001',
            'cancelmsg': '테스트 취소'
        }
        hash_fields = ['type', 'mid', 'tid', 'cancelmsg']
        hash_value = client._create_hash(test_params, hash_fields)
        print(f"해시 대상 파라미터: {test_params}")
        print(f"생성된 해시: {hash_value[:20]}...")
        
        await client.close()
        print("\n✅ KG이니시스 고급 예제 완료")
    
    else:
        print("❌ KG이니시스가 설정되지 않았습니다.")


async def kg_inicis_error_handling_example():
    """KG이니시스 에러 처리 예제"""
    print("\n=== KG이니시스 에러 처리 예제 ===")
    
    # 잘못된 설정으로 클라이언트 생성 시도
    try:
        config = Config(Environment.DEVELOPMENT)
        
        # 잘못된 설정 (INIAPI key 없음)
        wrong_config = PGConfig(
            merchant_id="INIpayTest",
            api_key="not_used",
            secret_key="",  # 빈 값
            api_base_url="https://iniapi.inicis.com"
        )
        
        config.add_pg_config(PGProvider.KG_INICIS, wrong_config)
        
        # 클라이언트 생성 시도 (실패해야 함)
        factory = PGClientFactory(config)
        client = factory.create_client(PGProvider.KG_INICIS)
        
    except Exception as e:
        print(f"✅ 예상된 설정 오류 발생: {e}")
    
    # IV 값이 없는 경우
    try:
        config = Config(Environment.DEVELOPMENT)
        
        wrong_config2 = PGConfig(
            merchant_id="INIpayTest",
            api_key="not_used",
            secret_key="ItEQKi3rY7uvDS8l",
            api_base_url="https://iniapi.inicis.com",
            extra_config={}  # IV 없음
        )
        
        config.add_pg_config(PGProvider.KG_INICIS, wrong_config2)
        factory = PGClientFactory(config)
        client = factory.create_client(PGProvider.KG_INICIS)
        
    except Exception as e:
        print(f"✅ 예상된 IV 오류 발생: {e}")
    
    print("\n✅ 에러 처리 예제 완료")


async def main():
    """KG이니시스 예제 실행"""
    print("🚀 KG이니시스 클라이언트 예제 시작")
    print("=" * 50)
    
    try:
        await kg_inicis_basic_example()
        await kg_inicis_advanced_example()
        await kg_inicis_error_handling_example()
        
    except Exception as e:
        print(f"❌ 전체 예제 실행 중 오류: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 KG이니시스 예제 완료")


if __name__ == "__main__":
    asyncio.run(main())
