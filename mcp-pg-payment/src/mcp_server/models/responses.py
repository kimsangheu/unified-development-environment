"""
API 응답 모델 정의
"""
from typing import Optional, Any, Dict, List, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

from .enums import PGProvider

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """통합 API 응답 모델"""
    success: bool = Field(..., description="성공 여부")
    data: Optional[T] = Field(None, description="응답 데이터")
    message: Optional[str] = Field(None, description="응답 메시지")
    code: Optional[str] = Field(None, description="응답 코드")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")
    provider: Optional[PGProvider] = Field(None, description="PG사 제공업체")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    success: bool = Field(False, description="성공 여부")
    error_code: str = Field(..., description="에러 코드")
    error_message: str = Field(..., description="에러 메시지")
    error_details: Optional[Dict[str, Any]] = Field(None, description="에러 상세 정보")
    timestamp: datetime = Field(default_factory=datetime.now, description="에러 발생 시간")
    provider: Optional[PGProvider] = Field(None, description="PG사 제공업체")
    
    # 디버깅 정보
    trace_id: Optional[str] = Field(None, description="추적 ID")
    request_id: Optional[str] = Field(None, description="요청 ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginationMeta(BaseModel):
    """페이지네이션 메타데이터"""
    current_page: int = Field(..., description="현재 페이지")
    per_page: int = Field(..., description="페이지당 항목 수")
    total_items: int = Field(..., description="전체 항목 수")
    total_pages: int = Field(..., description="전체 페이지 수")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")
    has_prev: bool = Field(..., description="이전 페이지 존재 여부")


class PaginatedResponse(BaseModel, Generic[T]):
    """페이지네이션이 적용된 응답 모델"""
    success: bool = Field(..., description="성공 여부")
    data: List[T] = Field(..., description="응답 데이터 목록")
    meta: PaginationMeta = Field(..., description="페이지네이션 메타데이터")
    message: Optional[str] = Field(None, description="응답 메시지")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")
    provider: Optional[PGProvider] = Field(None, description="PG사 제공업체")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaymentResponse(BaseModel):
    """결제 응답 모델"""
    payment_key: str = Field(..., description="결제 키")
    order_id: str = Field(..., description="주문 ID")
    amount: str = Field(..., description="결제 금액")
    status: str = Field(..., description="결제 상태")
    provider: PGProvider = Field(..., description="PG사 제공업체")
    
    # 선택적 필드
    redirect_url: Optional[str] = Field(None, description="리다이렉트 URL")
    checkout_url: Optional[str] = Field(None, description="결제 페이지 URL")
    qr_code: Optional[str] = Field(None, description="QR 코드")
    
    # 시간 정보
    requested_at: Optional[datetime] = Field(None, description="요청 시간")
    approved_at: Optional[datetime] = Field(None, description="승인 시간")
    
    # 추가 정보
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CancelResponse(BaseModel):
    """취소 응답 모델"""
    cancel_id: str = Field(..., description="취소 ID")
    payment_key: str = Field(..., description="결제 키")
    cancel_amount: str = Field(..., description="취소 금액")
    cancel_status: str = Field(..., description="취소 상태")
    provider: PGProvider = Field(..., description="PG사 제공업체")
    
    # 시간 정보
    requested_at: Optional[datetime] = Field(None, description="취소 요청 시간")
    canceled_at: Optional[datetime] = Field(None, description="취소 완료 시간")
    
    # 환불 정보
    refund_info: Optional[Dict[str, Any]] = Field(None, description="환불 정보")
    
    # 추가 정보
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookData(BaseModel):
    """웹훅 데이터 모델"""
    event_type: str = Field(..., description="이벤트 타입")
    payment_key: str = Field(..., description="결제 키")
    order_id: str = Field(..., description="주문 ID")
    status: str = Field(..., description="상태")
    provider: PGProvider = Field(..., description="PG사 제공업체")
    
    # 시간 정보
    created_at: datetime = Field(..., description="이벤트 발생 시간")
    
    # 추가 데이터
    data: Dict[str, Any] = Field(default_factory=dict, description="이벤트 데이터")
    
    # 검증 정보
    signature: Optional[str] = Field(None, description="서명")
    webhook_id: Optional[str] = Field(None, description="웹훅 ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthCheckResponse(BaseModel):
    """헬스 체크 응답 모델"""
    status: str = Field(..., description="서비스 상태")
    timestamp: datetime = Field(default_factory=datetime.now, description="체크 시간")
    version: Optional[str] = Field(None, description="버전 정보")
    providers: Dict[str, dict] = Field(default_factory=dict, description="PG사별 상태")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
