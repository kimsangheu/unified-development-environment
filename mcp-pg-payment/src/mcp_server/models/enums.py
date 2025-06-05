"""
결제 시스템의 열거형 정의
"""
from enum import Enum


class PGProvider(str, Enum):
    """PG사 제공업체 열거형"""
    KG_INICIS = "kg_inicis"
    NAVER_PAY = "naver_pay"
    KAKAO_PAY = "kakao_pay"
    NICE_PAYMENTS = "nice_payments"


class PaymentStatus(str, Enum):
    """결제 상태 열거형"""
    # 결제 진행 상태
    READY = "ready"                    # 결제 준비
    IN_PROGRESS = "in_progress"        # 결제 진행 중
    WAITING_FOR_DEPOSIT = "waiting_for_deposit"  # 입금 대기 (가상계좌)
    
    # 성공 상태
    DONE = "done"                      # 결제 완료
    CONFIRMED = "confirmed"            # 결제 승인 완료
    
    # 실패/취소 상태
    CANCELED = "canceled"              # 결제 취소
    FAILED = "failed"                  # 결제 실패
    EXPIRED = "expired"                # 결제 만료
    PARTIAL_CANCELED = "partial_canceled"  # 부분 취소
    
    # 기타
    UNKNOWN = "unknown"                # 알 수 없음


class PaymentMethod(str, Enum):
    """결제 수단 열거형"""
    # 카드
    CARD = "card"                      # 신용/체크카드
    
    # 간편결제
    KAKAO_PAY = "kakao_pay"           # 카카오페이
    NAVER_PAY = "naver_pay"           # 네이버페이
    SAMSUNG_PAY = "samsung_pay"       # 삼성페이
    PAYCO = "payco"                   # 페이코
    
    # 계좌이체
    TRANSFER = "transfer"              # 실시간 계좌이체
    VIRTUAL_ACCOUNT = "virtual_account"  # 가상계좌
    
    # 기타
    MOBILE = "mobile"                  # 휴대폰 소액결제
    POINT = "point"                    # 포인트
    GIFT_CERTIFICATE = "gift_certificate"  # 상품권
    
    UNKNOWN = "unknown"                # 알 수 없음


class CancelReason(str, Enum):
    """취소 사유 열거형"""
    CUSTOMER_REQUEST = "customer_request"        # 고객 요청
    ADMIN_REQUEST = "admin_request"              # 관리자 요청
    FRAUD_DETECTION = "fraud_detection"          # 사기 탐지
    PAYMENT_ERROR = "payment_error"              # 결제 오류
    INSUFFICIENT_FUNDS = "insufficient_funds"    # 잔액 부족
    EXPIRED = "expired"                          # 만료
    DUPLICATE = "duplicate"                      # 중복 결제
    OTHER = "other"                             # 기타


class TransactionType(str, Enum):
    """거래 유형 열거형"""
    PAYMENT = "payment"                # 결제
    CANCEL = "cancel"                  # 취소
    PARTIAL_CANCEL = "partial_cancel"  # 부분 취소
    REFUND = "refund"                  # 환불
