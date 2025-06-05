"""
PG사별 API 클라이언트 기본 구조
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union, Tuple
from datetime import datetime, timedelta
import aiohttp
from aiohttp import ClientTimeout, ClientSession

from ..config import PGConfig
from ..models.enums import PGProvider
from ..models.exceptions import PaymentException
from .exceptions import (
    PGHttpException,
    PGConnectionException,
    PGTimeoutException,
    PGAuthenticationException,
    PGConfigurationException,
    PGRateLimitException,
    PGResponseException,
    PGRetryExhaustedException
)


class BasePGClient(ABC):
    """PG사 API 클라이언트 추상 기본 클래스"""
    
    def __init__(self, config: PGConfig, provider: PGProvider):
        self.config = config
        self.provider = provider
        self.logger = logging.getLogger(f"pg_client.{provider.value}")
        self._session: Optional[ClientSession] = None
        self._session_created_at: Optional[datetime] = None
        self._session_timeout = timedelta(hours=1)  # 세션 재사용 시간 제한
        
        # 설정 검증
        self._validate_config()
    
    def _validate_config(self):
        """설정 검증"""
        if not self.config.merchant_id:
            raise PGConfigurationException(
                "merchant_id가 설정되지 않았습니다",
                provider=self.provider
            )
        
        if not self.config.api_key:
            raise PGConfigurationException(
                "api_key가 설정되지 않았습니다",
                provider=self.provider
            )
        
        if not self.config.api_base_url:
            raise PGConfigurationException(
                "api_base_url이 설정되지 않았습니다",
                provider=self.provider
            )
    
    async def _get_session(self) -> ClientSession:
        """HTTP 세션 반환 (재사용 및 자동 갱신)"""
        now = datetime.now()
        
        # 세션이 없거나 만료된 경우 새로 생성
        if (self._session is None or 
            self._session.closed or
            (self._session_created_at and 
             now - self._session_created_at > self._session_timeout)):
            
            if self._session and not self._session.closed:
                await self._session.close()
            
            timeout = ClientTimeout(total=self.config.timeout)
            connector = aiohttp.TCPConnector(
                limit=100,  # 최대 연결 수
                limit_per_host=30,  # 호스트당 최대 연결 수
                ttl_dns_cache=300,  # DNS 캐시 TTL
                use_dns_cache=True,
            )
            
            self._session = ClientSession(
                timeout=timeout,
                connector=connector,
                headers=self._get_default_headers(),
                raise_for_status=False  # 수동으로 상태 코드 처리
            )
            self._session_created_at = now
            
            self.logger.debug(f"새 HTTP 세션 생성: {self.provider.value}")
        
        return self._session
    
    def _get_default_headers(self) -> Dict[str, str]:
        """기본 HTTP 헤더 반환"""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"mcp-pg-payment/{self.provider.value}"
        }
    
    @abstractmethod
    def _get_auth_headers(self, **kwargs) -> Dict[str, str]:
        """인증 헤더 생성 (PG사별 구현 필요)"""
        pass
    
    def _build_url(self, endpoint: str) -> str:
        """완전한 URL 구성"""
        base_url = self.config.api_base_url.rstrip('/')
        endpoint = endpoint.lstrip('/')
        return f"{base_url}/{endpoint}"
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        auth_required: bool = True,
        **auth_kwargs
    ) -> Tuple[int, Dict[str, Any]]:
        """HTTP 요청 실행"""
        url = self._build_url(endpoint)
        session = await self._get_session()
        
        # 헤더 구성
        request_headers = self._get_default_headers()
        if auth_required:
            auth_headers = self._get_auth_headers(**auth_kwargs)
            request_headers.update(auth_headers)
        if headers:
            request_headers.update(headers)
        
        # 요청 데이터 준비
        json_data = data if data else None
        
        self.logger.debug(
            f"API 요청: {method} {url}",
            extra={
                "provider": self.provider.value,
                "endpoint": endpoint,
                "has_data": bool(data),
                "has_params": bool(params)
            }
        )
        
        # 재시도 로직과 함께 요청 실행
        return await self._execute_with_retry(
            session, method, url, json_data, params, request_headers
        )
    
    async def _execute_with_retry(
        self,
        session: ClientSession,
        method: str,
        url: str,
        json_data: Optional[Dict[str, Any]],
        params: Optional[Dict[str, Any]],
        headers: Dict[str, str]
    ) -> Tuple[int, Dict[str, Any]]:
        """재시도 로직과 함께 HTTP 요청 실행"""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                async with session.request(
                    method=method,
                    url=url,
                    json=json_data,
                    params=params,
                    headers=headers
                ) as response:
                    return await self._handle_response(response)
                    
            except asyncio.TimeoutError as e:
                last_exception = PGTimeoutException(
                    f"요청 타임아웃: {self.config.timeout}초",
                    timeout_seconds=self.config.timeout,
                    provider=self.provider
                )
                
            except aiohttp.ClientConnectionError as e:
                last_exception = PGConnectionException(
                    f"연결 실패: {str(e)}",
                    provider=self.provider
                )
                
            except Exception as e:
                last_exception = PGHttpException(
                    f"HTTP 요청 실패: {str(e)}",
                    status_code=0,
                    provider=self.provider
                )
            
            # 마지막 시도가 아니면 재시도 대기
            if attempt < self.config.max_retries:
                wait_time = self.config.retry_delay * (2 ** attempt)  # 지수 백오프
                self.logger.warning(
                    f"요청 실패, {wait_time}초 후 재시도 ({attempt + 1}/{self.config.max_retries}): {last_exception}",
                    extra={"provider": self.provider.value}
                )
                await asyncio.sleep(wait_time)
        
        # 모든 재시도 실패
        raise PGRetryExhaustedException(
            f"최대 재시도 횟수 초과: {last_exception}",
            attempts=self.config.max_retries + 1,
            provider=self.provider
        )
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Tuple[int, Dict[str, Any]]:
        """응답 처리"""
        status_code = response.status
        
        try:
            # 응답 본문 읽기
            text_content = await response.text()
            
            # JSON 파싱 시도
            try:
                response_data = json.loads(text_content) if text_content else {}
            except json.JSONDecodeError:
                response_data = {"raw_response": text_content}
            
            self.logger.debug(
                f"API 응답: {status_code}",
                extra={
                    "provider": self.provider.value,
                    "status_code": status_code,
                    "response_size": len(text_content)
                }
            )
            
            # 에러 상태 코드 처리
            if status_code >= 400:
                await self._handle_error_response(status_code, response_data, text_content)
            
            return status_code, response_data
            
        except Exception as e:
            raise PGResponseException(
                f"응답 처리 실패: {str(e)}",
                provider=self.provider
            )
    
    async def _handle_error_response(
        self, 
        status_code: int, 
        response_data: Dict[str, Any], 
        raw_response: str
    ):
        """에러 응답 처리"""
        if status_code == 401:
            raise PGAuthenticationException(
                "인증 실패",
                provider=self.provider,
                status_code=status_code,
                response_data=response_data
            )
        elif status_code == 429:
            retry_after = None
            if isinstance(response_data, dict):
                retry_after = response_data.get("retry_after")
            
            raise PGRateLimitException(
                "API 호출 제한 초과",
                retry_after=retry_after,
                provider=self.provider,
                status_code=status_code,
                response_data=response_data
            )
        else:
            error_message = self._extract_error_message(response_data)
            raise PGHttpException(
                error_message or f"HTTP 오류: {status_code}",
                status_code=status_code,
                provider=self.provider,
                response_data=response_data
            )
    
    def _extract_error_message(self, response_data: Dict[str, Any]) -> Optional[str]:
        """응답에서 에러 메시지 추출 (PG사별 오버라이드 가능)"""
        if isinstance(response_data, dict):
            # 일반적인 에러 메시지 필드들
            for field in ["message", "error", "error_message", "msg", "description"]:
                if field in response_data:
                    return str(response_data[field])
        return None
    
    # HTTP 메서드들
    async def get(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Tuple[int, Dict[str, Any]]:
        """GET 요청"""
        return await self._make_request("GET", endpoint, params=params, **kwargs)
    
    async def post(
        self, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Tuple[int, Dict[str, Any]]:
        """POST 요청"""
        return await self._make_request("POST", endpoint, data=data, **kwargs)
    
    async def put(
        self, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Tuple[int, Dict[str, Any]]:
        """PUT 요청"""
        return await self._make_request("PUT", endpoint, data=data, **kwargs)
    
    async def delete(
        self, 
        endpoint: str,
        **kwargs
    ) -> Tuple[int, Dict[str, Any]]:
        """DELETE 요청"""
        return await self._make_request("DELETE", endpoint, **kwargs)
    
    async def close(self):
        """클라이언트 종료 및 리소스 정리"""
        if self._session and not self._session.closed:
            await self._session.close()
            self.logger.debug(f"HTTP 세션 종료: {self.provider.value}")
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.close()
    
    # 추상 메서드들 - PG사별 구현 필요
    @abstractmethod
    async def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """결제 생성"""
        pass
    
    @abstractmethod
    async def confirm_payment(self, payment_key: str, order_id: str, amount: str) -> Dict[str, Any]:
        """결제 승인"""
        pass
    
    @abstractmethod
    async def get_payment(self, payment_key: str) -> Dict[str, Any]:
        """결제 조회"""
        pass
    
    @abstractmethod
    async def cancel_payment(self, payment_key: str, cancel_data: Dict[str, Any]) -> Dict[str, Any]:
        """결제 취소"""
        pass
    
    @abstractmethod
    async def verify_webhook(self, payload: str, signature: str) -> bool:
        """웹훅 검증"""
        pass
