"""
API 요청 모델 정의
"""
from typing import Optional, Dict, Any, List
from decimal import Decimal
from pydantic import BaseModel, Field, validator

from .enums import PaymentMethod, PGProvider, CancelReason


class PaymentRequest(BaseModel):
    """결제 요청 모델"""
    # 필수 필드
    order_id: str = Field(..., description="주문 ID", min_length=1, max_length=100)
    amount: Decimal = Field(..., description="결제 금액", ge=1)
    order_name: str = Field(..., description="주문명", min_length=1, max_length=100)
    method: PaymentMethod = Field(..., description="결제 수단")
    
    # 고객 정보
    customer_email: Optional[str] = Field(None, description="고객 이메일")
    customer_name: Optional[str] = Field(None, description="고객명", max_length=50)
    customer_mobile_phone: Optional[str] = Field(None, description="고객 휴대폰번호")
    
    # 결제 설정
    provider: Optional[PGProvider] = Field(None, description="사용할 PG사 (지정하지 않으면 자동 선택)")
    currency: str = Field("KRW", description="통화", max_length=3)
    
    # 성공/실패 URL
    success_url: Optional[str] = Field(None, description="결제 성공 시 리다이렉트 URL")
    fail_url: Optional[str] = Field(None, description="결제 실패 시 리다이렉트 URL")
    
    # 카드 결제 관련
    installment_plan_months: Optional[int] = Field(None, description="할부 개월수", ge=0, le=36)
    use_card_point: Optional[bool] = Field(None, description="카드포인트 사용 여부")
    
    # 가상계좌 관련
    virtual_account_due_date: Optional[str] = Field(None, description="가상계좌 입금 기한 (YYYY-MM-DD)")
    virtual_account_bank: Optional[str] = Field(None, description="가상계좌 은행 코드")
    
    # 기타 설정
    tax_free_amount: Optional[Decimal] = Field(None, description="비과세 금액", ge=0)
    vat_amount: Optional[Decimal] = Field(None, description="부가세", ge=0)
    supply_amount: Optional[Decimal] = Field(None, description="공급가액", ge=0)
    
    # 확장 데이터
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")

    @validator('customer_email')
    def validate_email(cls, v):
        if v is not None and '@' not in v:
            raise ValueError('올바른 이메일 형식이 아닙니다')
        return v

    @validator('amount', 'tax_free_amount', 'vat_amount', 'supply_amount')
    def validate_amounts(cls, v):
        if v is not None and v < 0:
            raise ValueError('금액은 0 이상이어야 합니다')
        return v

    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class CancelRequest(BaseModel):
    """취소 요청 모델"""
    # 필수 필드
    payment_key: str = Field(..., description="결제 키", min_length=1)
    cancel_reason: CancelReason = Field(..., description="취소 사유")
    
    # 부분 취소
    cancel_amount: Optional[Decimal] = Field(None, description="취소 금액 (전액 취소시 생략 가능)", ge=1)
    cancel_tax_free_amount: Optional[Decimal] = Field(None, description="취소 비과세 금액", ge=0)
    
    # 취소 상세 정보
    cancel_reason_detail: Optional[str] = Field(None, description="취소 상세 사유", max_length=200)
    
    # 환불 계좌 정보 (계좌이체, 가상계좌 환불시)
    refund_bank: Optional[str] = Field(None, description="환불 은행 코드")
    refund_account: Optional[str] = Field(None, description="환불 계좌번호")
    refund_holder_name: Optional[str] = Field(None, description="환불 계좌 예금주명")
    
    # 확장 데이터
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")

    @validator('cancel_amount', 'cancel_tax_free_amount')
    def validate_amounts(cls, v):
        if v is not None and v <= 0:
            raise ValueError('취소 금액은 0보다 커야 합니다')
        return v

    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class PaymentConfirmRequest(BaseModel):
    """결제 승인 요청 모델"""
    payment_key: str = Field(..., description="결제 키", min_length=1)
    order_id: str = Field(..., description="주문 ID", min_length=1)
    amount: Decimal = Field(..., description="결제 금액", ge=1)

    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class PaymentQueryRequest(BaseModel):
    """결제 조회 요청 모델"""
    # 조회 방식 (하나만 지정)
    payment_key: Optional[str] = Field(None, description="결제 키")
    order_id: Optional[str] = Field(None, description="주문 ID")
    
    # 조회 옵션
    include_canceled: bool = Field(False, description="취소된 결제 포함 여부")
    include_failed: bool = Field(False, description="실패한 결제 포함 여부")

    @validator('payment_key', 'order_id')
    def validate_query_params(cls, v, values):
        payment_key = values.get('payment_key')
        order_id = values.get('order_id')
        
        if not payment_key and not order_id:
            raise ValueError('payment_key 또는 order_id 중 하나는 필수입니다')
        if payment_key and order_id:
            raise ValueError('payment_key와 order_id 중 하나만 지정해야 합니다')
        return v


class BulkPaymentQueryRequest(BaseModel):
    """대량 결제 조회 요청 모델"""
    # 조회 조건
    start_date: Optional[str] = Field(None, description="시작 날짜 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="종료 날짜 (YYYY-MM-DD)")
    provider: Optional[PGProvider] = Field(None, description="PG사 필터")
    method: Optional[PaymentMethod] = Field(None, description="결제 수단 필터")
    status: Optional[List[str]] = Field(None, description="결제 상태 필터")
    
    # 페이징
    page: int = Field(1, description="페이지 번호", ge=1)
    limit: int = Field(20, description="페이지당 항목 수", ge=1, le=100)
    
    # 정렬
    sort_by: str = Field("created_at", description="정렬 기준")
    sort_order: str = Field("desc", description="정렬 순서 (asc/desc)")

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('정렬 순서는 asc 또는 desc만 가능합니다')
        return v


class WebhookRequest(BaseModel):
    """웹훅 요청 모델"""
    url: str = Field(..., description="웹훅 URL")
    events: List[str] = Field(..., description="구독할 이벤트 목록")
    secret: Optional[str] = Field(None, description="웹훅 검증용 시크릿")
    active: bool = Field(True, description="웹훅 활성화 여부")
    
    # 재시도 설정
    retry_count: int = Field(3, description="재시도 횟수", ge=0, le=10)
    retry_interval: int = Field(300, description="재시도 간격(초)", ge=60, le=3600)

    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('올바른 URL 형식이 아닙니다')
        return v


class RefundRequest(BaseModel):
    """환불 요청 모델"""
    payment_key: str = Field(..., description="결제 키", min_length=1)
    refund_amount: Optional[Decimal] = Field(None, description="환불 금액 (전액 환불시 생략 가능)", ge=1)
    refund_reason: str = Field(..., description="환불 사유", min_length=1, max_length=200)
    
    # 환불 계좌 정보
    refund_bank: str = Field(..., description="환불 은행 코드")
    refund_account: str = Field(..., description="환불 계좌번호")
    refund_holder_name: str = Field(..., description="환불 계좌 예금주명")
    
    # 확장 데이터
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")

    @validator('refund_amount')
    def validate_refund_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('환불 금액은 0보다 커야 합니다')
        return v

    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class ProviderConfigRequest(BaseModel):
    """PG사 설정 요청 모델"""
    provider: PGProvider = Field(..., description="PG사")
    
    # 인증 정보
    merchant_id: str = Field(..., description="가맹점 ID")
    api_key: str = Field(..., description="API 키")
    secret_key: Optional[str] = Field(None, description="시크릿 키")
    
    # 환경 설정
    is_production: bool = Field(False, description="운영 환경 여부")
    
    # API 설정
    api_url: Optional[str] = Field(None, description="API URL (기본값 사용시 생략)")
    timeout: int = Field(30, description="타임아웃(초)", ge=1, le=300)
    
    # 웹훅 설정
    webhook_url: Optional[str] = Field(None, description="웹훅 URL")
    webhook_secret: Optional[str] = Field(None, description="웹훅 시크릿")
    
    # 확장 설정
    extra_config: Dict[str, Any] = Field(default_factory=dict, description="PG사별 추가 설정")

    @validator('webhook_url')
    def validate_webhook_url(cls, v):
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError('올바른 웹훅 URL 형식이 아닙니다')
        return v
