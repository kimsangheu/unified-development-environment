"""
PG 클라이언트 관련 예외 클래스
"""
from typing import Optional, Dict, Any
from ..models.enums import PGProvider
from ..models.exceptions import PaymentException


class PGClientException(PaymentException):
    """PG 클라이언트 기본 예외"""
    
    def __init__(
        self,
        message: str,
        provider: Optional[PGProvider] = None,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(message, provider=provider, **kwargs)
        self.status_code = status_code
        self.response_data = response_data or {}
        
        if status_code:
            self.details["status_code"] = status_code
        if response_data:
            self.details["response_data"] = response_data


class PGHttpException(PGClientException):
    """HTTP 통신 관련 예외"""
    
    def __init__(self, message: str, status_code: int, **kwargs):
        super().__init__(
            message,
            code="PG_HTTP_ERROR",
            status_code=status_code,
            **kwargs
        )


class PGConnectionException(PGClientException):
    """연결 실패 예외"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            code="PG_CONNECTION_ERROR",
            **kwargs
        )


class PGTimeoutException(PGClientException):
    """타임아웃 예외"""
    
    def __init__(self, message: str, timeout_seconds: int, **kwargs):
        super().__init__(
            message,
            code="PG_TIMEOUT_ERROR",
            **kwargs
        )
        self.timeout_seconds = timeout_seconds
        self.details["timeout_seconds"] = timeout_seconds


class PGAuthenticationException(PGClientException):
    """인증 실패 예외"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            code="PG_AUTH_ERROR",
            **kwargs
        )


class PGConfigurationException(PGClientException):
    """설정 오류 예외"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            code="PG_CONFIG_ERROR",
            **kwargs
        )


class PGRateLimitException(PGClientException):
    """API 호출 제한 예외"""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(
            message,
            code="PG_RATE_LIMIT_ERROR",
            **kwargs
        )
        self.retry_after = retry_after
        if retry_after:
            self.details["retry_after"] = retry_after


class PGValidationException(PGClientException):
    """데이터 검증 실패 예외"""
    
    def __init__(self, message: str, validation_errors: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(
            message,
            code="PG_VALIDATION_ERROR",
            **kwargs
        )
        self.validation_errors = validation_errors or {}
        if validation_errors:
            self.details["validation_errors"] = validation_errors


class PGResponseException(PGClientException):
    """응답 처리 오류 예외"""
    
    def __init__(self, message: str, raw_response: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            code="PG_RESPONSE_ERROR",
            **kwargs
        )
        self.raw_response = raw_response
        if raw_response:
            self.details["raw_response"] = raw_response


class PGRetryExhaustedException(PGClientException):
    """재시도 횟수 초과 예외"""
    
    def __init__(self, message: str, attempts: int, **kwargs):
        super().__init__(
            message,
            code="PG_RETRY_EXHAUSTED",
            **kwargs
        )
        self.attempts = attempts
        self.details["attempts"] = attempts
