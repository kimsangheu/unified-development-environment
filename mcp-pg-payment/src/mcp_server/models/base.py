"""
기본 데이터 모델 정의
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator

from .enums import PGProvider, PaymentStatus, PaymentMethod, CancelReason, TransactionType


class Payment(BaseModel):
    """결제 기본 모델"""
    # 필수 필드
    payment_key: str = Field(..., description="결제 고유 키 (PG사에서 발급)")
    order_id: str = Field(..., description="주문 ID (가맹점에서 생성)")
    amount: Decimal = Field(..., description="결제 금액", ge=0)
    status: PaymentStatus = Field(..., description="결제 상태")
    method: PaymentMethod = Field(..., description="결제 수단")
    provider: PGProvider = Field(..., description="PG사 제공업체")
    
    # 선택 필드
    order_name: Optional[str] = Field(None, description="주문명")
    customer_email: Optional[str] = Field(None, description="고객 이메일")
    customer_name: Optional[str] = Field(None, description="고객명")
    customer_mobile_phone: Optional[str] = Field(None, description="고객 휴대폰번호")
    
    # 시간 정보
    requested_at: Optional[datetime] = Field(None, description="결제 요청 시간")
    approved_at: Optional[datetime] = Field(None, description="결제 승인 시간")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    updated_at: datetime = Field(default_factory=datetime.now, description="수정 시간")
    
    # 카드 정보 (카드 결제인 경우)
    card_company: Optional[str] = Field(None, description="카드사")
    card_number: Optional[str] = Field(None, description="카드번호 (마스킹)")
    card_type: Optional[str] = Field(None, description="카드 타입")
    
    # 가상계좌 정보 (가상계좌인 경우)
    virtual_account_bank: Optional[str] = Field(None, description="가상계좌 은행")
    virtual_account_number: Optional[str] = Field(None, description="가상계좌 번호")
    virtual_account_holder_name: Optional[str] = Field(None, description="가상계좌 예금주명")
    virtual_account_due_date: Optional[datetime] = Field(None, description="가상계좌 입금 기한")
    
    # 실패 정보
    failure_code: Optional[str] = Field(None, description="실패 코드")
    failure_reason: Optional[str] = Field(None, description="실패 사유")
    
    # PG사별 확장 데이터
    metadata: Dict[str, Any] = Field(default_factory=dict, description="PG사별 확장 데이터")
    
    # 원본 응답 데이터 (디버깅용)
    raw_data: Optional[Dict[str, Any]] = Field(None, description="PG사 원본 응답 데이터")

    @validator('amount')
    def validate_amount(cls, v):
        """금액 검증"""
        if v < 0:
            raise ValueError('금액은 0 이상이어야 합니다')
        return v

    @validator('customer_email')
    def validate_email(cls, v):
        """이메일 형식 검증"""
        if v is not None and '@' not in v:
            raise ValueError('올바른 이메일 형식이 아닙니다')
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }


class Transaction(BaseModel):
    """거래 추적 모델"""
    transaction_id: str = Field(..., description="거래 고유 ID")
    payment_key: str = Field(..., description="결제 키 (Payment 모델과 연결)")
    transaction_type: TransactionType = Field(..., description="거래 유형")
    
    # 금액 정보
    amount: Decimal = Field(..., description="거래 금액", ge=0)
    balance_amount: Optional[Decimal] = Field(None, description="잔여 금액")
    
    # 상태 정보
    status: PaymentStatus = Field(..., description="거래 상태")
    
    # 시간 정보
    requested_at: datetime = Field(..., description="거래 요청 시간")
    approved_at: Optional[datetime] = Field(None, description="거래 승인 시간")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    
    # PG사 정보
    provider: PGProvider = Field(..., description="PG사 제공업체")
    provider_transaction_id: Optional[str] = Field(None, description="PG사 거래 ID")
    
    # 실패 정보
    failure_code: Optional[str] = Field(None, description="실패 코드")
    failure_reason: Optional[str] = Field(None, description="실패 사유")
    
    # 확장 데이터
    metadata: Dict[str, Any] = Field(default_factory=dict, description="거래별 확장 데이터")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }


class Cancel(BaseModel):
    """취소 정보 모델"""
    cancel_id: str = Field(..., description="취소 고유 ID")
    payment_key: str = Field(..., description="결제 키 (Payment 모델과 연결)")
    transaction_id: Optional[str] = Field(None, description="관련 거래 ID")
    
    # 취소 금액 정보
    cancel_amount: Decimal = Field(..., description="취소 금액", ge=0)
    cancel_tax_free_amount: Optional[Decimal] = Field(None, description="취소 비과세 금액")
    cancel_reason: CancelReason = Field(..., description="취소 사유")
    cancel_reason_detail: Optional[str] = Field(None, description="취소 상세 사유")
    
    # 상태 정보
    cancel_status: PaymentStatus = Field(..., description="취소 상태")
    
    # 시간 정보
    canceled_at: Optional[datetime] = Field(None, description="취소 완료 시간")
    requested_at: datetime = Field(default_factory=datetime.now, description="취소 요청 시간")
    
    # PG사 정보
    provider: PGProvider = Field(..., description="PG사 제공업체")
    provider_cancel_id: Optional[str] = Field(None, description="PG사 취소 ID")
    
    # 환불 정보
    refund_bank: Optional[str] = Field(None, description="환불 은행")
    refund_account: Optional[str] = Field(None, description="환불 계좌")
    refund_holder_name: Optional[str] = Field(None, description="환불 계좌 예금주")
    
    # 실패 정보
    failure_code: Optional[str] = Field(None, description="실패 코드")
    failure_reason: Optional[str] = Field(None, description="실패 사유")
    
    # 확장 데이터
    metadata: Dict[str, Any] = Field(default_factory=dict, description="취소별 확장 데이터")

    @validator('cancel_amount')
    def validate_cancel_amount(cls, v):
        """취소 금액 검증"""
        if v <= 0:
            raise ValueError('취소 금액은 0보다 커야 합니다')
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }


class CustomerInfo(BaseModel):
    """고객 정보 모델"""
    customer_id: Optional[str] = Field(None, description="고객 ID")
    email: Optional[str] = Field(None, description="이메일")
    name: Optional[str] = Field(None, description="이름")
    mobile_phone: Optional[str] = Field(None, description="휴대폰번호")
    
    # 주소 정보
    address: Optional[str] = Field(None, description="주소")
    zipcode: Optional[str] = Field(None, description="우편번호")
    
    # 추가 정보
    birth_date: Optional[str] = Field(None, description="생년월일")
    gender: Optional[str] = Field(None, description="성별")


class CardInfo(BaseModel):
    """카드 정보 모델"""
    card_company: Optional[str] = Field(None, description="카드사")
    card_number: Optional[str] = Field(None, description="카드번호 (마스킹)")
    card_type: Optional[str] = Field(None, description="카드 타입 (신용/체크)")
    owner_type: Optional[str] = Field(None, description="소유자 타입 (개인/법인)")
    
    # 할부 정보
    installment_plan_months: Optional[int] = Field(None, description="할부 개월수")
    interest_free_install: Optional[bool] = Field(None, description="무이자 할부 여부")
    
    # 승인 정보
    approve_no: Optional[str] = Field(None, description="승인번호")
    use_card_point: Optional[bool] = Field(None, description="카드포인트 사용 여부")


class VirtualAccountInfo(BaseModel):
    """가상계좌 정보 모델"""
    bank_code: str = Field(..., description="은행 코드")
    bank_name: str = Field(..., description="은행명")
    account_number: str = Field(..., description="계좌번호")
    holder_name: str = Field(..., description="예금주명")
    due_date: Optional[datetime] = Field(None, description="입금 기한")
    
    # 상태 정보
    settlement_status: Optional[str] = Field(None, description="정산 상태")
    refund_status: Optional[str] = Field(None, description="환불 상태")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
