"""
결제 시스템 예외 클래스 정의
"""
from typing import Optional, Dict, Any
from .enums import PGProvider


class PaymentException(Exception):
    """결제 시스템 기본 예외 클래스"""
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        provider: Optional[PGProvider] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.provider = provider
        self.details = details or {}

    def __str__(self):
        return f"[{self.code or 'UNKNOWN'}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """예외를 딕셔너리로 변환"""
        return {
            "error_code": self.code,
            "error_message": self.message,
            "provider": self.provider,
            "details": self.details
        }


class PaymentValidationError(PaymentException):
    """결제 데이터 검증 오류"""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(message, code="VALIDATION_ERROR", **kwargs)
        self.field = field
        if field:
            self.details["field"] = field


class PaymentNotFoundError(PaymentException):
    """결제 정보를 찾을 수 없음"""
    
    def __init__(self, payment_key: str, **kwargs):
        super().__init__(
            f"결제 정보를 찾을 수 없습니다: {payment_key}",
            code="PAYMENT_NOT_FOUND",
            **kwargs
        )
        self.payment_key = payment_key
        self.details["payment_key"] = payment_key


class PaymentStatusError(PaymentException):
    """결제 상태 오류"""
    
    def __init__(self, message: str, current_status: str, expected_status: str = None, **kwargs):
        super().__init__(message, code="PAYMENT_STATUS_ERROR", **kwargs)
        self.current_status = current_status
        self.expected_status = expected_status
        self.details.update({
            "current_status": current_status,
            "expected_status": expected_status
        })


class PaymentAmountMismatchError(PaymentException):
    """결제 금액 불일치 오류"""
    
    def __init__(self, requested_amount: str, actual_amount: str, **kwargs):
        super().__init__(
            f"결제 금액이 일치하지 않습니다. 요청: {requested_amount}, 실제: {actual_amount}",
            code="AMOUNT_MISMATCH",
            **kwargs
        )
        self.requested_amount = requested_amount
        self.actual_amount = actual_amount
        self.details.update({
            "requested_amount": requested_amount,
            "actual_amount": actual_amount
        })


class PGProviderError(PaymentException):
    """PG사 관련 오류"""
    
    def __init__(self, message: str, provider: PGProvider, pg_error_code: str = None, **kwargs):
        super().__init__(
            message,
            code="PG_PROVIDER_ERROR",
            provider=provider,
            **kwargs
        )
        self.pg_error_code = pg_error_code
        if pg_error_code:
            self.details["pg_error_code"] = pg_error_code


class PGProviderTimeoutError(PGProviderError):
    """PG사 API 타임아웃 오류"""
    
    def __init__(self, provider: PGProvider, timeout_seconds: int, **kwargs):
        super().__init__(
            f"PG사 API 타임아웃: {timeout_seconds}초",
            provider=provider,
            **kwargs
        )
        self.code = "PG_TIMEOUT"
        self.timeout_seconds = timeout_seconds
        self.details["timeout_seconds"] = timeout_seconds


class PGProviderUnavailableError(PGProviderError):
    """PG사 서비스 이용 불가 오류"""
    
    def __init__(self, provider: PGProvider, **kwargs):
        super().__init__(
            f"PG사 서비스를 이용할 수 없습니다: {provider}",
            provider=provider,
            **kwargs
        )
        self.code = "PG_UNAVAILABLE"


class PaymentCancelError(PaymentException):
    """결제 취소 오류"""
    
    def __init__(self, message: str, payment_key: str, **kwargs):
        super().__init__(message, code="CANCEL_ERROR", **kwargs)
        self.payment_key = payment_key
        self.details["payment_key"] = payment_key


class PaymentRefundError(PaymentException):
    """결제 환불 오류"""
    
    def __init__(self, message: str, payment_key: str, **kwargs):
        super().__init__(message, code="REFUND_ERROR", **kwargs)
        self.payment_key = payment_key
        self.details["payment_key"] = payment_key


class PaymentConfigurationError(PaymentException):
    """결제 설정 오류"""
    
    def __init__(self, message: str, provider: Optional[PGProvider] = None, **kwargs):
        super().__init__(
            message,
            code="CONFIGURATION_ERROR",
            provider=provider,
            **kwargs
        )


class PaymentAuthenticationError(PaymentException):
    """결제 인증 오류"""
    
    def __init__(self, message: str, provider: Optional[PGProvider] = None, **kwargs):
        super().__init__(
            message,
            code="AUTHENTICATION_ERROR",
            provider=provider,
            **kwargs
        )


class PaymentNetworkError(PaymentException):
    """네트워크 연결 오류"""
    
    def __init__(self, message: str, provider: Optional[PGProvider] = None, **kwargs):
        super().__init__(
            message,
            code="NETWORK_ERROR",
            provider=provider,
            **kwargs
        )


class PaymentFraudError(PaymentException):
    """결제 사기 탐지 오류"""
    
    def __init__(self, message: str, payment_key: str, reason: str, **kwargs):
        super().__init__(message, code="FRAUD_DETECTED", **kwargs)
        self.payment_key = payment_key
        self.reason = reason
        self.details.update({
            "payment_key": payment_key,
            "fraud_reason": reason
        })


class PaymentLimitExceededError(PaymentException):
    """결제 한도 초과 오류"""
    
    def __init__(self, message: str, limit_type: str, limit_amount: str, **kwargs):
        super().__init__(message, code="LIMIT_EXCEEDED", **kwargs)
        self.limit_type = limit_type
        self.limit_amount = limit_amount
        self.details.update({
            "limit_type": limit_type,
            "limit_amount": limit_amount
        })


class WebhookVerificationError(PaymentException):
    """웹훅 검증 오류"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="WEBHOOK_VERIFICATION_ERROR", **kwargs)


class PaymentDuplicateError(PaymentException):
    """중복 결제 오류"""
    
    def __init__(self, order_id: str, **kwargs):
        super().__init__(
            f"이미 존재하는 주문입니다: {order_id}",
            code="DUPLICATE_PAYMENT",
            **kwargs
        )
        self.order_id = order_id
        self.details["order_id"] = order_id


# 예외 매핑 딕셔너리 (PG사별 에러 코드 매핑용)
PG_ERROR_MAPPING = {
    # KG이니시스 에러 코드 매핑 예시
    "kg_inicis": {
        "00": PaymentException,  # 성공
        "01": PaymentValidationError,  # 파라미터 오류
        "02": PaymentAuthenticationError,  # 인증 오류
        "03": PaymentAmountMismatchError,  # 금액 불일치
        "04": PaymentStatusError,  # 상태 오류
        "05": PaymentCancelError,  # 취소 불가
        "99": PGProviderError,  # 기타 오류
    },
    # 다른 PG사들도 추가 가능
}


def create_pg_exception(
    provider: PGProvider,
    pg_error_code: str,
    message: str,
    **kwargs
) -> PaymentException:
    """PG사 에러 코드를 기반으로 적절한 예외 생성"""
    provider_mapping = PG_ERROR_MAPPING.get(provider.value, {})
    exception_class = provider_mapping.get(pg_error_code, PGProviderError)
    
    return exception_class(
        message=message,
        provider=provider,
        pg_error_code=pg_error_code,
        **kwargs
    )
