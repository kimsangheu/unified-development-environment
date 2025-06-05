"""
KG이니시스 응답 매퍼
"""
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

from ...models.base import Payment, Transaction, Cancel
from ...models.enums import PGProvider, PaymentStatus, PaymentMethod, CancelReason, TransactionType


class KGInicisResponseMapper:
    """KG이니시스 응답을 공통 모델로 변환하는 매퍼"""
    
    @staticmethod
    def to_payment(response_data: Dict[str, Any]) -> Payment:
        """KG이니시스 응답을 Payment 모델로 변환"""
        
        # 기본 필드 매핑
        payment_data = {
            'payment_key': response_data.get('tid', ''),
            'order_id': response_data.get('oid', ''),
            'amount': Decimal(str(response_data.get('price', '0'))),
            'status': KGInicisResponseMapper._map_payment_status(response_data.get('resultCode')),
            'method': KGInicisResponseMapper._map_payment_method(response_data.get('paymethod')),
            'provider': PGProvider.KG_INICIS,
        }
        
        # 선택적 필드들
        if 'goodname' in response_data:
            payment_data['order_name'] = response_data['goodname']
        
        if 'buyername' in response_data:
            payment_data['customer_name'] = response_data['buyername']
        
        if 'buyeremail' in response_data:
            payment_data['customer_email'] = response_data['buyeremail']
        
        if 'buyertel' in response_data:
            payment_data['customer_mobile_phone'] = response_data['buyertel']
        
        # 시간 정보
        if 'authdate' in response_data:
            payment_data['approved_at'] = KGInicisResponseMapper._parse_datetime(response_data['authdate'])
        
        if 'reqdate' in response_data:
            payment_data['requested_at'] = KGInicisResponseMapper._parse_datetime(response_data['reqdate'])
        
        # 카드 정보
        if response_data.get('paymethod') == 'Card':
            payment_data.update({
                'card_company': response_data.get('cardname'),
                'card_number': response_data.get('cardnum'),  # 이미 마스킹됨
                'card_type': response_data.get('cardtype'),
            })
        
        # 가상계좌 정보  
        elif response_data.get('paymethod') == 'VCard':
            payment_data.update({
                'virtual_account_bank': response_data.get('bankname'),
                'virtual_account_number': response_data.get('vacct'),
                'virtual_account_holder_name': response_data.get('vaname'),
            })
            
            if 'vadate' in response_data:
                payment_data['virtual_account_due_date'] = KGInicisResponseMapper._parse_datetime(response_data['vadate'])
        
        # 실패 정보
        if response_data.get('resultCode') != '00':
            payment_data.update({
                'failure_code': response_data.get('resultCode'),
                'failure_reason': response_data.get('resultMsg'),
            })
        
        # 원본 데이터 저장
        payment_data['raw_data'] = response_data
        
        return Payment(**payment_data)
    
    @staticmethod
    def to_transaction(response_data: Dict[str, Any], transaction_type: TransactionType) -> Transaction:
        """KG이니시스 응답을 Transaction 모델로 변환"""
        
        transaction_data = {
            'transaction_id': response_data.get('tid', ''),
            'payment_key': response_data.get('tid', ''),
            'transaction_type': transaction_type,
            'amount': Decimal(str(response_data.get('price', '0'))),
            'status': KGInicisResponseMapper._map_payment_status(response_data.get('resultCode')),
            'provider': PGProvider.KG_INICIS,
            'provider_transaction_id': response_data.get('tid'),
        }
        
        # 시간 정보
        if 'authdate' in response_data:
            transaction_data['approved_at'] = KGInicisResponseMapper._parse_datetime(response_data['authdate'])
            transaction_data['requested_at'] = transaction_data['approved_at']  # KG이니시스는 동일
        
        # 실패 정보
        if response_data.get('resultCode') != '00':
            transaction_data.update({
                'failure_code': response_data.get('resultCode'),
                'failure_reason': response_data.get('resultMsg'),
            })
        
        # 메타데이터
        transaction_data['metadata'] = {
            'kg_inicis_data': response_data
        }
        
        return Transaction(**transaction_data)
    
    @staticmethod
    def to_cancel(response_data: Dict[str, Any], original_payment_key: str) -> Cancel:
        """KG이니시스 응답을 Cancel 모델로 변환"""
        
        cancel_data = {
            'cancel_id': response_data.get('tid', ''),
            'payment_key': original_payment_key,
            'cancel_amount': Decimal(str(response_data.get('price', '0'))),
            'cancel_reason': CancelReason.ADMIN_REQUEST,  # 기본값
            'cancel_status': KGInicisResponseMapper._map_payment_status(response_data.get('resultCode')),
            'provider': PGProvider.KG_INICIS,
            'provider_cancel_id': response_data.get('tid'),
        }
        
        # 취소 상세 사유
        if 'cancelmsg' in response_data:
            cancel_data['cancel_reason_detail'] = response_data['cancelmsg']
        
        # 시간 정보
        if 'canceldate' in response_data:
            cancel_data['canceled_at'] = KGInicisResponseMapper._parse_datetime(response_data['canceldate'])
        
        # 환불 계좌 정보
        if 'refundAcctNum' in response_data:
            cancel_data.update({
                'refund_account': response_data['refundAcctNum'],
                'refund_bank': response_data.get('refundBankCode'),
                'refund_holder_name': response_data.get('refundAcctName'),
            })
        
        # 실패 정보
        if response_data.get('resultCode') != '00':
            cancel_data.update({
                'failure_code': response_data.get('resultCode'),
                'failure_reason': response_data.get('resultMsg'),
            })
        
        # 메타데이터
        cancel_data['metadata'] = {
            'kg_inicis_data': response_data
        }
        
        return Cancel(**cancel_data)
    
    @staticmethod
    def _map_payment_status(result_code: str) -> PaymentStatus:
        """KG이니시스 결과 코드를 PaymentStatus로 매핑"""
        status_map = {
            '00': PaymentStatus.DONE,           # 성공
            '01': PaymentStatus.FAILED,         # 실패
            '02': PaymentStatus.CANCELED,       # 취소됨
            '03': PaymentStatus.READY,          # 대기중
            '04': PaymentStatus.IN_PROGRESS,    # 진행중
            '05': PaymentStatus.WAITING_FOR_DEPOSIT,  # 입금대기
            '99': PaymentStatus.EXPIRED,        # 만료
        }
        
        return status_map.get(str(result_code), PaymentStatus.UNKNOWN)
    
    @staticmethod
    def _map_payment_method(paymethod: str) -> PaymentMethod:
        """KG이니시스 결제수단을 PaymentMethod로 매핑"""
        method_map = {
            'Card': PaymentMethod.CARD,                    # 신용카드
            'VCard': PaymentMethod.VIRTUAL_ACCOUNT,        # 가상계좌
            'HPP': PaymentMethod.MOBILE,                   # 휴대폰 소액결제
            'Bank': PaymentMethod.TRANSFER,                # 계좌이체
            'SSG': PaymentMethod.SAMSUNG_PAY,              # 삼성페이
            'KakaoPay': PaymentMethod.KAKAO_PAY,          # 카카오페이
            'NaverPay': PaymentMethod.NAVER_PAY,          # 네이버페이
            'PAYCO': PaymentMethod.PAYCO,                 # 페이코
            'Point': PaymentMethod.POINT,                 # 포인트
            'Giftcard': PaymentMethod.GIFT_CERTIFICATE,   # 상품권
        }
        
        return method_map.get(str(paymethod), PaymentMethod.UNKNOWN)
    
    @staticmethod
    def _parse_datetime(date_str: str) -> Optional[datetime]:
        """KG이니시스 날짜 문자열을 datetime으로 변환"""
        if not date_str:
            return None
        
        try:
            # KG이니시스 날짜 형식: YYYYMMDDHHMMSS
            if len(date_str) == 14:
                return datetime.strptime(date_str, '%Y%m%d%H%M%S')
            # 다른 형식들도 지원
            elif len(date_str) == 8:
                return datetime.strptime(date_str, '%Y%m%d')
            else:
                return None
        except ValueError:
            return None


class KGInicisRequestMapper:
    """공통 모델을 KG이니시스 요청으로 변환하는 매퍼"""
    
    @staticmethod
    def from_payment_data(payment_data: Dict[str, Any]) -> Dict[str, str]:
        """공통 결제 데이터를 KG이니시스 요청 파라미터로 변환"""
        
        # 결제수단 매핑
        method_map = {
            PaymentMethod.CARD: 'Card',
            PaymentMethod.VIRTUAL_ACCOUNT: 'VCard',
            PaymentMethod.MOBILE: 'HPP',
            PaymentMethod.TRANSFER: 'Bank',
            PaymentMethod.SAMSUNG_PAY: 'SSG',
            PaymentMethod.KAKAO_PAY: 'KakaoPay',
            PaymentMethod.NAVER_PAY: 'NaverPay',
            PaymentMethod.PAYCO: 'PAYCO',
        }
        
        kg_params = {
            'paymethod': method_map.get(payment_data.get('method'), 'Card'),
            'oid': payment_data.get('order_id', ''),
            'price': str(payment_data.get('amount', 0)),
            'goodname': payment_data.get('order_name', '상품명'),
            'buyername': payment_data.get('buyer_name', '구매자'),
            'buyeremail': payment_data.get('buyer_email', ''),
            'buyertel': payment_data.get('buyer_tel', ''),
        }
        
        # 선택적 파라미터들
        if 'buyer_addr' in payment_data:
            kg_params['buyeraddr'] = payment_data['buyer_addr']
        
        if 'buyer_postcode' in payment_data:
            kg_params['buyerpostcode'] = payment_data['buyer_postcode']
        
        # 가상계좌 특화 설정
        if payment_data.get('method') == PaymentMethod.VIRTUAL_ACCOUNT:
            if 'va_due_date' in payment_data:
                # KG이니시스 가상계좌 입금기한 형식으로 변환
                kg_params['vadate'] = payment_data['va_due_date']
        
        # 할부 설정 (카드 결제)
        if payment_data.get('method') == PaymentMethod.CARD:
            if 'installment' in payment_data:
                kg_params['quotabase'] = str(payment_data['installment'])
        
        return kg_params
    
    @staticmethod
    def from_cancel_data(cancel_data: Dict[str, Any]) -> Dict[str, str]:
        """공통 취소 데이터를 KG이니시스 요청 파라미터로 변환"""
        
        kg_params = {
            'type': 'cancel',
            'cancelmsg': cancel_data.get('reason', '관리자 취소'),
        }
        
        # 부분 취소 금액
        if 'cancel_amount' in cancel_data:
            kg_params['price'] = str(cancel_data['cancel_amount'])
        
        # 환불 계좌 정보 (가상계좌 환불시)
        if 'refund_account' in cancel_data:
            kg_params.update({
                'refundAcctNum': cancel_data['refund_account'],  # [ENC] 필드
                'refundBankCode': cancel_data.get('refund_bank_code', ''),
                'refundAcctName': cancel_data.get('refund_holder_name', ''),
            })
        
        return kg_params
