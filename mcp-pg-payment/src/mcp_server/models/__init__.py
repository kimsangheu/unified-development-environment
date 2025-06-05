"""
결제 시스템 모델 패키지

이 패키지는 PG사들과의 통합을 위한 공통 데이터 모델을 제공합니다.
Pydantic 기반으로 타입 안정성과 데이터 검증을 보장합니다.
"""

# 열거형 import
from .enums import (
    PGProvider,
    PaymentStatus,
    PaymentMethod,
    CancelReason,
    TransactionType
)

# 기본 모델 import
from .base import (
    Payment,
    Transaction,
    Cancel,
    CustomerInfo,
    CardInfo,
    VirtualAccountInfo
)

# 응답 모델 import
from .responses import (
    ApiResponse,
    ErrorResponse,
    PaginationMeta,
    PaginatedResponse,
    PaymentResponse,
    CancelResponse,
    WebhookData,
    HealthCheckResponse
)

# 요청 모델 import
from .requests import (
    PaymentRequest,
    CancelRequest,
    PaymentConfirmRequest,
    PaymentQueryRequest,
    BulkPaymentQueryRequest,
    WebhookRequest,
    RefundRequest,
    ProviderConfigRequest
)

# 예외 클래스 import
from .exceptions import (
    PaymentException,
    PaymentValidationError,
    PaymentNotFoundError,
    PaymentStatusError,
    PaymentAmountMismatchError,
    PGProviderError,
    PGProviderTimeoutError,
    PGProviderUnavailableError,
    PaymentCancelError,
    PaymentRefundError,
    PaymentConfigurationError,
    PaymentAuthenticationError,
    PaymentNetworkError,
    PaymentFraudError,
    PaymentLimitExceededError,
    WebhookVerificationError,
    PaymentDuplicateError,
    create_pg_exception
)

# 유틸리티 함수 import
from .utils import (
    generate_payment_key,
    generate_transaction_id,
    mask_card_number,
    mask_phone_number,
    validate_email,
    validate_phone_number,
    format_amount,
    calculate_vat,
    calculate_supply_amount,
    normalize_payment_status,
    normalize_payment_method,
    create_signature,
    verify_signature,
    encode_base64,
    decode_base64,
    create_basic_auth_header,
    parse_webhook_data,
    format_datetime_for_pg,
    parse_pg_datetime,
    sanitize_order_id,
    generate_random_string,
    is_valid_amount_range,
    get_pg_test_card_numbers,
    extract_error_info,
    build_redirect_url,
    get_current_timestamp,
    calculate_business_days
)

__all__ = [
    # 열거형
    "PGProvider",
    "PaymentStatus", 
    "PaymentMethod",
    "CancelReason",
    "TransactionType",
    
    # 기본 모델
    "Payment",
    "Transaction",
    "Cancel",
    "CustomerInfo",
    "CardInfo",
    "VirtualAccountInfo",
    
    # 응답 모델
    "ApiResponse",
    "ErrorResponse",
    "PaginationMeta",
    "PaginatedResponse",
    "PaymentResponse",
    "CancelResponse",
    "WebhookData",
    "HealthCheckResponse",
    
    # 요청 모델
    "PaymentRequest",
    "CancelRequest",
    "PaymentConfirmRequest",
    "PaymentQueryRequest",
    "BulkPaymentQueryRequest",
    "WebhookRequest",
    "RefundRequest",
    "ProviderConfigRequest",
    
    # 예외 클래스
    "PaymentException",
    "PaymentValidationError",
    "PaymentNotFoundError",
    "PaymentStatusError",
    "PaymentAmountMismatchError",
    "PGProviderError",
    "PGProviderTimeoutError",
    "PGProviderUnavailableError",
    "PaymentCancelError",
    "PaymentRefundError",
    "PaymentConfigurationError",
    "PaymentAuthenticationError",
    "PaymentNetworkError",
    "PaymentFraudError",
    "PaymentLimitExceededError",
    "WebhookVerificationError",
    "PaymentDuplicateError",
    "create_pg_exception",
    
    # 유틸리티 함수
    "generate_payment_key",
    "generate_transaction_id",
    "mask_card_number",
    "mask_phone_number",
    "validate_email",
    "validate_phone_number",
    "format_amount",
    "calculate_vat",
    "calculate_supply_amount",
    "normalize_payment_status",
    "normalize_payment_method",
    "create_signature",
    "verify_signature",
    "encode_base64",
    "decode_base64",
    "create_basic_auth_header",
    "parse_webhook_data",
    "format_datetime_for_pg",
    "parse_pg_datetime",
    "sanitize_order_id",
    "generate_random_string",
    "is_valid_amount_range",
    "get_pg_test_card_numbers",
    "extract_error_info",
    "build_redirect_url",
    "get_current_timestamp",
    "calculate_business_days"
]

# 모델 버전 정보
__version__ = "1.0.0"

# 지원하는 PG사 목록
SUPPORTED_PROVIDERS = [
    PGProvider.KG_INICIS,
    PGProvider.NAVER_PAY,
    PGProvider.KAKAO_PAY,
    PGProvider.NICE_PAYMENTS
]

# 지원하는 결제 수단 목록
SUPPORTED_PAYMENT_METHODS = [
    PaymentMethod.CARD,
    PaymentMethod.KAKAO_PAY,
    PaymentMethod.NAVER_PAY,
    PaymentMethod.SAMSUNG_PAY,
    PaymentMethod.PAYCO,
    PaymentMethod.TRANSFER,
    PaymentMethod.VIRTUAL_ACCOUNT,
    PaymentMethod.MOBILE,
    PaymentMethod.POINT,
    PaymentMethod.GIFT_CERTIFICATE
]
