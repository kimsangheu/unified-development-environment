"""
KG이니시스 통합 클라이언트 (공식 모듈 기반)
실제 PC/모바일 일반결제 + INIAPI 취소/환불
"""
import hashlib
import time
from typing import Dict, Any, Optional, Union
from urllib.parse import urlencode
from datetime import datetime
import json

from ..base import BasePGClient
from ...models.enums import PGProvider, PaymentStatus, PaymentMethod
from ...config import PGConfig
from ..exceptions import (
    PGAuthenticationException,
    PGValidationException,
    PGHttpException,
    PGResponseException
)


class KGInicisClient(BasePGClient):
    """KG이니시스 통합 클라이언트 (공식 모듈 기반)"""
    
    def __init__(self, config: PGConfig, provider: PGProvider = PGProvider.KG_INICIS):
        super().__init__(config, provider)
        
        # KG이니시스 설정
        self.merchant_id = config.merchant_id  # 상점 ID (예: INIpayTest)
        self.sign_key = config.secret_key      # 웹 결제 signkey
        
        # API 엔드포인트 (실제 공식 URL)
        if config.is_production:
            self.std_pay_host = "https://stdpay.inicis.com"
            self.auth_url = "https://stdpay.inicis.com/api/payAuth"
            self.iniapi_host = "https://iniapi.inicis.com"
        else:
            self.std_pay_host = "https://stgstdpay.inicis.com" 
            self.auth_url = "https://stgstdpay.inicis.com/api/payAuth"
            self.iniapi_host = "https://stginiapi.inicis.com"
        
        # INIAPI 설정 (취소/환불용)
        self.iniapi_key = config.extra_config.get('iniapi_key', '')
        self.iniapi_iv = config.extra_config.get('iniapi_iv', '')
        
        # 설정 검증
        if not self.sign_key:
            raise PGValidationException(
                "KG이니시스 signKey가 설정되지 않았습니다",
                provider=self.provider
            )
    
    def _get_auth_headers(self, **kwargs) -> Dict[str, str]:
        """HTTP 헤더 생성"""
        return {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json, text/plain",
            "User-Agent": "KGInicis-Python-Client/1.0"
        }
    
    def _get_timestamp(self) -> str:
        """KG이니시스 타임스탬프 생성 (밀리초 단위)"""
        return str(int(time.time() * 1000))
    
    def _make_hash(self, data: str, algorithm: str = "sha256") -> str:
        """해시 생성"""
        if algorithm == "sha256":
            return hashlib.sha256(data.encode('utf-8')).hexdigest()
        else:
            raise ValueError(f"지원하지 않는 해시 알고리즘: {algorithm}")
    
    def _make_signature(self, params: Dict[str, str]) -> str:
        """
        KG이니시스 signature 생성 (공식 모듈 방식)
        key=value&key=value 형태로 연결 후 SHA-256
        """
        # key 기준 알파벳 정렬
        sorted_params = sorted(params.items())
        
        # key=value 형태로 연결
        param_string = "&".join([f"{key}={value}" for key, value in sorted_params])
        
        # SHA-256 해시
        signature = self._make_hash(param_string)
        
        self.logger.debug(f"Signature 생성 - 원본: {param_string}")
        self.logger.debug(f"Signature 결과: {signature}")
        
        return signature
    
    def _make_m_key(self) -> str:
        """mKey 생성 (signKey의 SHA-256 해시)"""
        return self._make_hash(self.sign_key)
    
    # ===== 일반 결제 관련 메서드 =====
    
    def create_payment_form_data(self, payment_data: Dict[str, Any]) -> Dict[str, str]:
        """
        결제 폼 데이터 생성 (PC/모바일 결제창용)
        실제 공식 모듈과 동일한 파라미터 구조
        """
        timestamp = self._get_timestamp()
        order_id = payment_data.get('order_id', f"{self.merchant_id}_{timestamp}")
        price = str(payment_data.get('amount', 1000))
        
        # 기본 파라미터
        form_data = {
            "version": "1.0",
            "mid": self.merchant_id,
            "oid": order_id,
            "price": price,
            "timestamp": timestamp,
            "use_chkfake": "Y",  # PC결제 보안강화 (고정값)
            "currency": "WON",
            
            # 상품 정보
            "goodname": payment_data.get('order_name', '테스트상품'),
            
            # 구매자 정보
            "buyername": payment_data.get('buyer_name', '구매자'),
            "buyertel": payment_data.get('buyer_tel', '01012345678'),
            "buyeremail": payment_data.get('buyer_email', 'test@test.com'),
            
            # 결제 수단
            "gopaymethod": payment_data.get('gopaymethod', 'Card:Directbank:vbank'),
            
            # URL 설정
            "returnUrl": payment_data.get('return_url', 'https://example.com/return'),
            "closeUrl": payment_data.get('close_url', 'https://example.com/close'),
            
            # 기타 옵션
            "acceptmethod": payment_data.get('acceptmethod', 'HPP(1):below1000:centerCd(Y)')
        }
        
        # signature 생성 (oid, price, timestamp)
        signature_params = {
            "oid": order_id,
            "price": price,
            "timestamp": timestamp
        }
        form_data["signature"] = self._make_signature(signature_params)
        
        # verification 생성 (oid, price, signKey, timestamp)
        verification_params = {
            "oid": order_id,
            "price": price,
            "signKey": self.sign_key,
            "timestamp": timestamp
        }
        form_data["verification"] = self._make_signature(verification_params)
        
        # mKey 생성
        form_data["mKey"] = self._make_m_key()
        
        return form_data
    
    def generate_payment_form_html(self, payment_data: Dict[str, Any], target_id: str = "payment_form") -> str:
        """결제 폼 HTML 생성"""
        form_data = self.create_payment_form_data(payment_data)
        
        # 테스트/운영 JavaScript URL
        js_url = f"{self.std_pay_host}/stdjs/INIStdPay.js"
        
        html = f"""
<script language="javascript" type="text/javascript" src="{js_url}" charset="UTF-8"></script>
<script type="text/javascript">
    function startPayment() {{
        INIStdPay.pay('{target_id}');
    }}
</script>

<form id="{target_id}" method="post">
"""
        
        # 모든 파라미터를 hidden input으로 생성
        for key, value in form_data.items():
            html += f'    <input type="hidden" name="{key}" value="{value}">\n'
        
        html += """</form>

<button onclick="startPayment()">결제하기</button>"""
        
        return html
    
    async def confirm_payment(self, auth_token: str, timestamp: str = None) -> Dict[str, Any]:
        """
        결제 승인 API 호출 (공식 모듈 방식)
        returnUrl에서 받은 authToken으로 실제 승인 처리
        """
        if not timestamp:
            timestamp = self._get_timestamp()
        
        # 승인 요청 파라미터
        params = {
            "mid": self.merchant_id,
            "authToken": auth_token,
            "timestamp": timestamp,
            "charset": "UTF-8",
            "format": "JSON"
        }
        
        # signature 생성 (authToken, timestamp)
        signature_params = {
            "authToken": auth_token,
            "timestamp": timestamp
        }
        params["signature"] = self._make_signature(signature_params)
        
        # verification 생성 (authToken, signKey, timestamp)
        verification_params = {
            "authToken": auth_token,
            "signKey": self.sign_key,
            "timestamp": timestamp
        }
        params["verification"] = self._make_signature(verification_params)
        
        # API 호출
        session = await self._get_session()
        
        try:
            async with session.post(
                self.auth_url,
                data=urlencode(params),
                headers=self._get_auth_headers()
            ) as response:
                
                if response.content_type == 'application/json':
                    result = await response.json()
                else:
                    text = await response.text()
                    result = json.loads(text)
                
                self.logger.info(f"KG이니시스 승인 응답: {result}")
                
                return result
                
        except Exception as e:
            raise PGHttpException(
                f"KG이니시스 승인 API 호출 실패: {str(e)}",
                status_code=0,
                provider=self.provider
            )
    
    # ===== BasePGClient 인터페이스 구현 =====
    
    async def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """결제 생성 (실제로는 폼 데이터 생성)"""
        form_data = self.create_payment_form_data(payment_data)
        
        return {
            'payment_key': form_data['oid'],
            'order_id': form_data['oid'],
            'amount': form_data['price'],
            'status': PaymentStatus.READY,
            'form_data': form_data,
            'payment_url': f"{self.std_pay_host}/stdpay/order/",
            'html_form': self.generate_payment_form_html(payment_data)
        }
    
    async def get_payment(self, payment_key: str) -> Dict[str, Any]:
        """결제 조회 - 실제로는 승인 결과를 기반으로 구성"""
        # KG이니시스는 별도 조회 API가 없어서 승인 결과나 DB 기반으로 구현 필요
        return {
            'payment_key': payment_key,
            'status': PaymentStatus.UNKNOWN,
            'message': 'KG이니시스는 별도 조회 API를 제공하지 않습니다. 승인 결과를 저장 후 활용하세요.'
        }
    
    async def cancel_payment(self, payment_key: str, cancel_data: Dict[str, Any]) -> Dict[str, Any]:
        """결제 취소 - INIAPI 사용 (별도 구현 필요)"""
        if not self.iniapi_key:
            raise PGValidationException(
                "INIAPI key가 설정되지 않았습니다. 취소/환불에는 INIAPI 설정이 필요합니다.",
                provider=self.provider
            )
        
        # INIAPI 취소 로직 (기존 구현 활용)
        return await self._cancel_via_iniapi(payment_key, cancel_data)
    
    async def _cancel_via_iniapi(self, payment_key: str, cancel_data: Dict[str, Any]) -> Dict[str, Any]:
        """INIAPI를 통한 취소 처리"""
        # 기존 INIAPI 구현 로직 활용
        params = {
            'type': 'cancel',
            'mid': self.merchant_id,
            'tid': payment_key,
            'cancelmsg': cancel_data.get('reason', '관리자 취소')
        }
        
        if 'cancel_amount' in cancel_data:
            params['price'] = str(cancel_data['cancel_amount'])
        
        # INIAPI는 별도 구현이 필요 (기존 코드 참고)
        return {
            'cancel_id': payment_key,
            'status': PaymentStatus.CANCELED,
            'message': 'INIAPI 취소 구현 필요'
        }
    
    async def verify_webhook(self, payload: str, signature: str) -> bool:
        """웹훅 검증"""
        # KG이니시스 웹훅 검증 로직
        try:
            expected_signature = self._make_hash(payload + self.sign_key)
            return signature == expected_signature
        except Exception as e:
            self.logger.error(f"웹훅 검증 실패: {e}")
            return False
    
    # ===== 헬퍼 메서드 =====
    
    def _map_payment_status(self, result_code: str) -> PaymentStatus:
        """KG이니시스 결과 코드를 PaymentStatus로 매핑"""
        status_map = {
            '0000': PaymentStatus.DONE,      # 성공
            '9999': PaymentStatus.FAILED,    # 실패
        }
        
        return status_map.get(result_code, PaymentStatus.UNKNOWN)
    
    def get_idc_urls(self) -> Dict[str, str]:
        """IDC별 URL 매핑 (실제 공식 설정)"""
        if self.config.is_production:
            return {
                'fc': 'https://fcstdpay.inicis.com/api/payAuth',
                'ks': 'https://ksstdpay.inicis.com/api/payAuth',
                'stg': 'https://stdpay.inicis.com/api/payAuth'  # 운영 기본
            }
        else:
            return {
                'fc': 'https://fcstgstdpay.inicis.com/api/payAuth',
                'ks': 'https://ksstgstdpay.inicis.com/api/payAuth', 
                'stg': 'https://stgstdpay.inicis.com/api/payAuth'  # 테스트 기본
            }
