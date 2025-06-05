"""
결제 시스템 유틸리티 함수들
"""
import re
import hashlib
import hmac
import base64
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any, Union
from urllib.parse import urlencode, parse_qs

from .enums import PaymentStatus, PaymentMethod, PGProvider


def generate_payment_key(provider: PGProvider, order_id: str) -> str:
    """결제 키 생성"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{provider.value}_{timestamp}_{order_id}_{unique_id}"


def generate_transaction_id() -> str:
    """거래 ID 생성"""
    return str(uuid.uuid4())


def mask_card_number(card_number: str) -> str:
    """카드번호 마스킹"""
    if not card_number or len(card_number) < 8:
        return card_number
    
    # 앞 4자리와 뒤 4자리만 표시
    return f"{card_number[:4]}****{card_number[-4:]}"


def mask_phone_number(phone: str) -> str:
    """휴대폰번호 마스킹"""
    if not phone:
        return phone
    
    # 010-1234-5678 -> 010-****-5678
    phone = re.sub(r'[^0-9]', '', phone)
    if len(phone) == 11:
        return f"{phone[:3]}-****-{phone[-4:]}"
    return phone


def validate_email(email: str) -> bool:
    """이메일 형식 검증"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone_number(phone: str) -> bool:
    """휴대폰번호 형식 검증 (한국)"""
    phone = re.sub(r'[^0-9]', '', phone)
    pattern = r'^01[0-9]{8,9}$'
    return bool(re.match(pattern, phone))


def format_amount(amount: Union[str, int, float, Decimal]) -> Decimal:
    """금액 포맷팅 (소수점 반올림)"""
    if isinstance(amount, str):
        amount = Decimal(amount)
    elif isinstance(amount, (int, float)):
        amount = Decimal(str(amount))
    
    return amount.quantize(Decimal('1'), rounding=ROUND_HALF_UP)


def calculate_vat(amount: Decimal, vat_rate: Decimal = Decimal('0.1')) -> Decimal:
    """부가세 계산"""
    vat = amount * vat_rate
    return vat.quantize(Decimal('1'), rounding=ROUND_HALF_UP)


def calculate_supply_amount(total_amount: Decimal, vat_amount: Decimal) -> Decimal:
    """공급가액 계산"""
    return total_amount - vat_amount


def normalize_payment_status(status: str, provider: PGProvider) -> PaymentStatus:
    """PG사별 결제 상태를 표준 상태로 변환"""
    status_mapping = {
        PGProvider.KG_INICIS: {
            "paid": PaymentStatus.DONE,
            "ready": PaymentStatus.READY,
            "failed": PaymentStatus.FAILED,
            "cancelled": PaymentStatus.CANCELED,
            "partial_cancelled": PaymentStatus.PARTIAL_CANCELED,
            "waiting_for_deposit": PaymentStatus.WAITING_FOR_DEPOSIT,
        },
        PGProvider.PORTONE: {
            "paid": PaymentStatus.DONE,
            "ready": PaymentStatus.READY,
            "failed": PaymentStatus.FAILED,
            "cancelled": PaymentStatus.CANCELED,
            "partial_cancelled": PaymentStatus.PARTIAL_CANCELED,
        },
        # 다른 PG사들도 추가 가능
    }
    
    provider_mapping = status_mapping.get(provider, {})
    return provider_mapping.get(status.lower(), PaymentStatus.UNKNOWN)


def normalize_payment_method(method: str, provider: PGProvider) -> PaymentMethod:
    """PG사별 결제 수단을 표준 수단으로 변환"""
    method_mapping = {
        PGProvider.KG_INICIS: {
            "card": PaymentMethod.CARD,
            "trans": PaymentMethod.TRANSFER,
            "vbank": PaymentMethod.VIRTUAL_ACCOUNT,
            "phone": PaymentMethod.MOBILE,
            "kakaopay": PaymentMethod.KAKAO_PAY,
            "naverpay": PaymentMethod.NAVER_PAY,
            "samsungpay": PaymentMethod.SAMSUNG_PAY,
            "payco": PaymentMethod.PAYCO,
        },
        PGProvider.PORTONE: {
            "card": PaymentMethod.CARD,
            "trans": PaymentMethod.TRANSFER,
            "vbank": PaymentMethod.VIRTUAL_ACCOUNT,
            "phone": PaymentMethod.MOBILE,
            "kakaopay": PaymentMethod.KAKAO_PAY,
            "naverpay": PaymentMethod.NAVER_PAY,
        },
        # 다른 PG사들도 추가 가능
    }
    
    provider_mapping = method_mapping.get(provider, {})
    return provider_mapping.get(method.lower(), PaymentMethod.UNKNOWN)


def create_signature(data: Dict[str, Any], secret_key: str, algorithm: str = "sha256") -> str:
    """서명 생성 (웹훅 검증용)"""
    # 데이터를 정렬된 쿼리 스트링으로 변환
    sorted_items = sorted(data.items())
    query_string = urlencode(sorted_items)
    
    # HMAC 서명 생성
    if algorithm == "sha256":
        signature = hmac.new(
            secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    elif algorithm == "sha1":
        signature = hmac.new(
            secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha1
        ).hexdigest()
    else:
        raise ValueError(f"지원하지 않는 알고리즘: {algorithm}")
    
    return signature


def verify_signature(data: Dict[str, Any], signature: str, secret_key: str, algorithm: str = "sha256") -> bool:
    """서명 검증"""
    expected_signature = create_signature(data, secret_key, algorithm)
    return hmac.compare_digest(signature, expected_signature)


def encode_base64(data: str) -> str:
    """Base64 인코딩"""
    return base64.b64encode(data.encode('utf-8')).decode('utf-8')


def decode_base64(encoded_data: str) -> str:
    """Base64 디코딩"""
    return base64.b64decode(encoded_data).decode('utf-8')


def create_basic_auth_header(username: str, password: str) -> str:
    """Basic 인증 헤더 생성"""
    credentials = f"{username}:{password}"
    encoded_credentials = encode_base64(credentials)
    return f"Basic {encoded_credentials}"


def parse_webhook_data(raw_data: str, content_type: str = "application/json") -> Dict[str, Any]:
    """웹훅 데이터 파싱"""
    import json
    
    if content_type == "application/json":
        return json.loads(raw_data)
    elif content_type == "application/x-www-form-urlencoded":
        return dict(parse_qs(raw_data, keep_blank_values=True))
    else:
        raise ValueError(f"지원하지 않는 Content-Type: {content_type}")


def format_datetime_for_pg(dt: datetime, provider: PGProvider) -> str:
    """PG사별 날짜 형식으로 변환"""
    format_mapping = {
        PGProvider.KG_INICIS: "%Y%m%d%H%M%S",
        PGProvider.PORTONE: "%Y-%m-%dT%H:%M:%S+09:00",
        # 다른 PG사들도 추가
    }
    
    date_format = format_mapping.get(provider, "%Y-%m-%dT%H:%M:%S")
    return dt.strftime(date_format)


def parse_pg_datetime(date_string: str, provider: PGProvider) -> Optional[datetime]:
    """PG사 날짜 문자열을 datetime 객체로 변환"""
    if not date_string:
        return None
    
    format_mapping = {
        PGProvider.KG_INICIS: "%Y%m%d%H%M%S",
        PGProvider.PORTONE: "%Y-%m-%dT%H:%M:%S+09:00",
    }
    
    date_format = format_mapping.get(provider)
    if not date_format:
        # 기본 ISO 형식으로 시도
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except ValueError:
            return None
    
    try:
        return datetime.strptime(date_string, date_format)
    except ValueError:
        return None


def sanitize_order_id(order_id: str) -> str:
    """주문 ID 정제 (특수문자 제거)"""
    # 알파벳, 숫자, 하이픈, 언더스코어만 허용
    return re.sub(r'[^a-zA-Z0-9_-]', '', order_id)


def generate_random_string(length: int = 32) -> str:
    """랜덤 문자열 생성"""
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def is_valid_amount_range(amount: Decimal, min_amount: Decimal = Decimal('100'), max_amount: Decimal = Decimal('10000000')) -> bool:
    """결제 금액 범위 검증"""
    return min_amount <= amount <= max_amount


def get_pg_test_card_numbers(provider: PGProvider) -> Dict[str, str]:
    """PG사별 테스트 카드번호 반환"""
    test_cards = {
        PGProvider.KG_INICIS: {
            "신한카드": "4092730100000000",
            "KB국민카드": "4210123456789012",
            "삼성카드": "4239123456789012",
            "현대카드": "4329123456789012",
        },
        PGProvider.PORTONE: {
            "테스트카드": "4000000000000002",
            "실패카드": "4000000000000259",
        },
    }
    
    return test_cards.get(provider, {})


def extract_error_info(error_response: Dict[str, Any], provider: PGProvider) -> Dict[str, str]:
    """PG사 에러 응답에서 에러 정보 추출"""
    error_mapping = {
        PGProvider.KG_INICIS: {
            "code_field": "resultCode",
            "message_field": "resultMsg",
        },
        PGProvider.PORTONE: {
            "code_field": "code",
            "message_field": "message",
        },
    }
    
    mapping = error_mapping.get(provider, {"code_field": "code", "message_field": "message"})
    
    return {
        "code": error_response.get(mapping["code_field"], "UNKNOWN"),
        "message": error_response.get(mapping["message_field"], "알 수 없는 오류")
    }


def build_redirect_url(base_url: str, params: Dict[str, Any]) -> str:
    """리다이렉트 URL 생성"""
    query_string = urlencode(params)
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{query_string}"


def get_current_timestamp() -> str:
    """현재 타임스탬프 반환 (ISO 형식)"""
    return datetime.now(timezone.utc).isoformat()


def calculate_business_days(start_date: datetime, days: int) -> datetime:
    """영업일 계산 (주말 제외)"""
    current_date = start_date
    business_days = 0
    
    while business_days < days:
        current_date += timedelta(days=1)
        # 주말이 아닌 경우에만 영업일로 카운트
        if current_date.weekday() < 5:  # 0=월요일, 4=금요일
            business_days += 1
    
    return current_date
