"""
통합 결제 서비스

여러 PG사를 통합하여 관리하는 통합 결제 서비스를 제공합니다.
팩토리 패턴을 활용하여 환경설정에 따라 적절한 PG사 클라이언트를 선택하고 관리합니다.
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum

from ..models.base import BasePaymentRequest, BasePaymentResponse
from ..models.requests import (
    PaymentRequest, 
    PaymentCancelRequest, 
    PaymentStatusRequest
)
from ..models.responses import (
    PaymentResponse, 
    PaymentCancelResponse, 
    PaymentStatusResponse
)
from ..models.enums import PGProvider, PaymentStatus, PaymentMethod
from ..models.exceptions import (
    PaymentException, 
    PGException, 
    PGConfigurationException,
    PaymentValidationException
)
from ..pg_handlers.factory import PGClientFactory, PGClientManager
from ..pg_handlers.base import BasePGClient
from ..config import Config, get_config


logger = logging.getLogger(__name__)


class PaymentServiceMode(Enum):
    """결제 서비스 모드"""
    SINGLE = "single"  # 단일 PG사 모드
    MULTI = "multi"    # 다중 PG사 모드 (폴백 지원)
    ROUND_ROBIN = "round_robin"  # 라운드 로빈 방식


class PaymentServiceStrategy(Enum):
    """결제 처리 전략"""
    FAIL_FAST = "fail_fast"  # 첫 번째 실패 시 즉시 중단
    RETRY_ALL = "retry_all"  # 모든 PG사에서 재시도
    BEST_EFFORT = "best_effort"  # 최선 노력 (일부 실패 허용)


class PaymentServiceConfig:
    """결제 서비스 설정"""
    
    def __init__(
        self,
        mode: PaymentServiceMode = PaymentServiceMode.MULTI,
        strategy: PaymentServiceStrategy = PaymentServiceStrategy.BEST_EFFORT,
        primary_provider: Optional[PGProvider] = None,
        fallback_providers: Optional[List[PGProvider]] = None,
        max_retry_attempts: int = 3,
        retry_delay_seconds: float = 1.0,
        timeout_seconds: float = 30.0,
        enable_circuit_breaker: bool = True
    ):
        self.mode = mode
        self.strategy = strategy
        self.primary_provider = primary_provider
        self.fallback_providers = fallback_providers or []
        self.max_retry_attempts = max_retry_attempts
        self.retry_delay_seconds = retry_delay_seconds
        self.timeout_seconds = timeout_seconds
        self.enable_circuit_breaker = enable_circuit_breaker


class PaymentService:
    """
    통합 결제 서비스
    
    여러 PG사를 통합하여 관리하고, 팩토리 패턴을 활용하여
    환경설정에 따라 적절한 PG사 클라이언트를 선택합니다.
    """
    
    def __init__(
        self,
        config: Optional[Config] = None,
        service_config: Optional[PaymentServiceConfig] = None,
        pg_client_manager: Optional[PGClientManager] = None
    ):
        self.config = config or get_config()
        self.service_config = service_config or PaymentServiceConfig()
        self.pg_client_manager = pg_client_manager or PGClientManager()
        
        # 상태 관리
        self._provider_status: Dict[PGProvider, Dict[str, Any]] = {}
        self._provider_last_used: Dict[PGProvider, datetime] = {}
        self._round_robin_index = 0
        
        logger.info(f"PaymentService 초기화 완료 - 모드: {self.service_config.mode}")
    
    async def process_payment(
        self, 
        request: PaymentRequest,
        preferred_provider: Optional[PGProvider] = None
    ) -> PaymentResponse:
        """
        결제 처리
        
        Args:
            request: 결제 요청 정보
            preferred_provider: 선호하는 PG사 (옵션)
            
        Returns:
            PaymentResponse: 결제 처리 결과
            
        Raises:
            PaymentException: 결제 처리 실패
            PaymentValidationException: 요청 데이터 검증 실패
        """
        logger.info(f"결제 처리 시작 - 주문번호: {request.order_id}")
        
        # 요청 검증
        self._validate_payment_request(request)
        
        try:
            # PG사 선택 전략에 따라 처리
            if self.service_config.mode == PaymentServiceMode.SINGLE:
                return await self._process_single_payment(request, preferred_provider)
            elif self.service_config.mode == PaymentServiceMode.MULTI:
                return await self._process_multi_payment(request, preferred_provider)
            elif self.service_config.mode == PaymentServiceMode.ROUND_ROBIN:
                return await self._process_round_robin_payment(request)
            else:
                raise PaymentException(f"지원하지 않는 서비스 모드: {self.service_config.mode}")
                
        except Exception as e:
            logger.error(f"결제 처리 실패 - 주문번호: {request.order_id}, 오류: {str(e)}")
            
            # PaymentException이 아닌 경우 래핑
            if not isinstance(e, PaymentException):
                raise PaymentException(f"결제 처리 중 오류 발생: {str(e)}") from e
            raise
    
    async def get_payment_status(
        self, 
        request: PaymentStatusRequest,
        provider: Optional[PGProvider] = None
    ) -> PaymentStatusResponse:
        """
        결제 상태 조회
        
        Args:
            request: 결제 상태 조회 요청
            provider: 특정 PG사 지정 (옵션)
            
        Returns:
            PaymentStatusResponse: 결제 상태 조회 결과
        """
        logger.info(f"결제 상태 조회 - 주문번호: {request.order_id}")
        
        if provider:
            # 특정 PG사 지정
            client = await self.pg_client_manager.get_client(provider)
            return await client.get_payment_status(request)
        else:
            # 모든 사용 가능한 PG사에서 조회 시도
            return await self._get_payment_status_with_fallback(request)
    
    async def cancel_payment(
        self, 
        request: PaymentCancelRequest,
        provider: Optional[PGProvider] = None
    ) -> PaymentCancelResponse:
        """
        결제 취소
        
        Args:
            request: 결제 취소 요청
            provider: 특정 PG사 지정 (옵션)
            
        Returns:
            PaymentCancelResponse: 결제 취소 결과
        """
        logger.info(f"결제 취소 시작 - 주문번호: {request.order_id}")
        
        if provider:
            # 특정 PG사 지정
            client = await self.pg_client_manager.get_client(provider)
            return await client.cancel_payment(request)
        else:
            # 모든 사용 가능한 PG사에서 취소 시도
            return await self._cancel_payment_with_fallback(request)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        서비스 상태 확인
        
        Returns:
            Dict: 서비스 및 PG사별 상태 정보
        """
        logger.debug("헬스체크 수행")
        
        status = {
            "service": {
                "status": "healthy",
                "mode": self.service_config.mode.value,
                "strategy": self.service_config.strategy.value,
                "timestamp": datetime.now().isoformat()
            },
            "providers": await self._get_providers_health()
        }
        
        return status
    
    def _validate_payment_request(self, request: PaymentRequest):
        """결제 요청 검증"""
        if not request.order_id:
            raise PaymentValidationException("주문번호가 필요합니다")
        
        if not request.amount or request.amount <= 0:
            raise PaymentValidationException("결제 금액은 0보다 커야 합니다")
        
        if not request.customer_info or not request.customer_info.name:
            raise PaymentValidationException("고객 정보가 필요합니다")
    
    async def _process_single_payment(
        self, 
        request: PaymentRequest,
        preferred_provider: Optional[PGProvider] = None
    ) -> PaymentResponse:
        """단일 PG사 결제 처리"""
        provider = preferred_provider or self.service_config.primary_provider
        
        if not provider:
            available_providers = self.pg_client_manager.factory.get_available_providers()
            if not available_providers:
                raise PGConfigurationException("사용 가능한 PG사가 없습니다")
            provider = available_providers[0]
        
        client = await self.pg_client_manager.get_client(provider)
        return await self._execute_payment_with_retry(client, request)
    
    async def _process_multi_payment(
        self, 
        request: PaymentRequest,
        preferred_provider: Optional[PGProvider] = None
    ) -> PaymentResponse:
        """다중 PG사 폴백 결제 처리"""
        # 시도 순서 결정
        providers_to_try = self._get_payment_provider_order(preferred_provider)
        
        if not providers_to_try:
            raise PGConfigurationException("사용 가능한 PG사가 없습니다")
        
        last_exception = None
        
        for provider in providers_to_try:
            try:
                logger.info(f"PG사 시도: {provider.value}")
                client = await self.pg_client_manager.get_client(provider)
                
                response = await self._execute_payment_with_retry(client, request)
                
                # 성공 시 상태 업데이트
                self._update_provider_status(provider, True)
                self._provider_last_used[provider] = datetime.now()
                
                logger.info(f"결제 성공 - PG사: {provider.value}, 주문번호: {request.order_id}")
                return response
                
            except Exception as e:
                logger.warning(f"PG사 결제 실패 - {provider.value}: {str(e)}")
                self._update_provider_status(provider, False)
                last_exception = e
                
                # FAIL_FAST 전략이면 즉시 중단
                if self.service_config.strategy == PaymentServiceStrategy.FAIL_FAST:
                    break
                
                # 다음 PG사로 계속 시도
                continue
        
        # 모든 PG사에서 실패
        logger.error(f"모든 PG사에서 결제 실패 - 주문번호: {request.order_id}")
        raise PaymentException(f"결제 처리 실패: {str(last_exception)}") from last_exception
    
    async def _process_round_robin_payment(
        self, 
        request: PaymentRequest
    ) -> PaymentResponse:
        """라운드 로빈 방식 결제 처리"""
        available_providers = self.pg_client_manager.factory.get_available_providers()
        
        if not available_providers:
            raise PGConfigurationException("사용 가능한 PG사가 없습니다")
        
        # 라운드 로빈으로 PG사 선택
        provider = available_providers[self._round_robin_index % len(available_providers)]
        self._round_robin_index += 1
        
        client = await self.pg_client_manager.get_client(provider)
        return await self._execute_payment_with_retry(client, request)
    
    async def _execute_payment_with_retry(
        self, 
        client: BasePGClient, 
        request: PaymentRequest
    ) -> PaymentResponse:
        """재시도 로직을 포함한 결제 실행"""
        last_exception = None
        
        for attempt in range(self.service_config.max_retry_attempts):
            try:
                # 타임아웃 설정
                return await asyncio.wait_for(
                    client.process_payment(request),
                    timeout=self.service_config.timeout_seconds
                )
                
            except asyncio.TimeoutError:
                last_exception = PaymentException("결제 처리 시간 초과")
            except Exception as e:
                last_exception = e
                
                # 재시도 불가능한 오류인 경우 즉시 중단
                if isinstance(e, PaymentValidationException):
                    raise
            
            # 재시도 전 대기
            if attempt < self.service_config.max_retry_attempts - 1:
                await asyncio.sleep(self.service_config.retry_delay_seconds)
        
        # 모든 재시도 실패
        raise PaymentException(f"재시도 후에도 결제 실패: {str(last_exception)}") from last_exception
    
    async def _get_payment_status_with_fallback(
        self, 
        request: PaymentStatusRequest
    ) -> PaymentStatusResponse:
        """폴백을 포함한 결제 상태 조회"""
        available_providers = self.pg_client_manager.factory.get_available_providers()
        
        for provider in available_providers:
            try:
                client = await self.pg_client_manager.get_client(provider)
                response = await client.get_payment_status(request)
                
                # 결제 정보를 찾은 경우 반환
                if response.status != PaymentStatus.NOT_FOUND:
                    return response
                    
            except Exception as e:
                logger.warning(f"상태 조회 실패 - {provider.value}: {str(e)}")
                continue
        
        # 모든 PG사에서 찾지 못함
        return PaymentStatusResponse(
            order_id=request.order_id,
            status=PaymentStatus.NOT_FOUND,
            message="결제 정보를 찾을 수 없습니다"
        )
    
    async def _cancel_payment_with_fallback(
        self, 
        request: PaymentCancelRequest
    ) -> PaymentCancelResponse:
        """폴백을 포함한 결제 취소"""
        available_providers = self.pg_client_manager.factory.get_available_providers()
        
        for provider in available_providers:
            try:
                client = await self.pg_client_manager.get_client(provider)
                return await client.cancel_payment(request)
                
            except Exception as e:
                logger.warning(f"결제 취소 실패 - {provider.value}: {str(e)}")
                continue
        
        # 모든 PG사에서 실패
        raise PaymentException("결제 취소에 실패했습니다")
    
    def _get_payment_provider_order(
        self, 
        preferred_provider: Optional[PGProvider] = None
    ) -> List[PGProvider]:
        """결제 시도 PG사 순서 결정"""
        available_providers = self.pg_client_manager.factory.get_available_providers()
        
        if not available_providers:
            return []
        
        # 선호 PG사가 있고 사용 가능하면 맨 앞에 배치
        if preferred_provider and preferred_provider in available_providers:
            providers = [preferred_provider]
            providers.extend([p for p in available_providers if p != preferred_provider])
            return providers
        
        # 기본 PG사가 설정되어 있으면 맨 앞에 배치
        if self.service_config.primary_provider and self.service_config.primary_provider in available_providers:
            providers = [self.service_config.primary_provider]
            providers.extend([p for p in available_providers if p != self.service_config.primary_provider])
            return providers
        
        # 폴백 순서가 설정되어 있으면 해당 순서 적용
        if self.service_config.fallback_providers:
            providers = []
            for provider in self.service_config.fallback_providers:
                if provider in available_providers:
                    providers.append(provider)
            
            # 나머지 PG사들 추가
            for provider in available_providers:
                if provider not in providers:
                    providers.append(provider)
            
            return providers
        
        # 기본적으로는 사용 가능한 순서대로
        return available_providers
    
    def _update_provider_status(self, provider: PGProvider, success: bool):
        """PG사 상태 업데이트"""
        if provider not in self._provider_status:
            self._provider_status[provider] = {
                "success_count": 0,
                "failure_count": 0,
                "last_success": None,
                "last_failure": None
            }
        
        status = self._provider_status[provider]
        now = datetime.now()
        
        if success:
            status["success_count"] += 1
            status["last_success"] = now
        else:
            status["failure_count"] += 1
            status["last_failure"] = now
    
    async def _get_providers_health(self) -> Dict[str, Dict[str, Any]]:
        """PG사별 상태 정보 조회"""
        health_info = {}
        
        for provider in PGProvider:
            try:
                is_available = self.pg_client_manager.factory.is_provider_available(provider)
                status_info = self._provider_status.get(provider, {})
                
                health_info[provider.value] = {
                    "available": is_available,
                    "configured": self.config.is_configured(provider),
                    "success_count": status_info.get("success_count", 0),
                    "failure_count": status_info.get("failure_count", 0),
                    "last_success": status_info.get("last_success"),
                    "last_failure": status_info.get("last_failure"),
                    "last_used": self._provider_last_used.get(provider)
                }
                
            except Exception as e:
                health_info[provider.value] = {
                    "available": False,
                    "error": str(e)
                }
        
        return health_info
    
    async def close(self):
        """서비스 종료 및 리소스 정리"""
        logger.info("PaymentService 종료")
        await self.pg_client_manager.close_all()
    
    def get_service_info(self) -> Dict[str, Any]:
        """서비스 정보 반환"""
        return {
            "mode": self.service_config.mode.value,
            "strategy": self.service_config.strategy.value,
            "primary_provider": self.service_config.primary_provider.value if self.service_config.primary_provider else None,
            "fallback_providers": [p.value for p in self.service_config.fallback_providers],
            "max_retry_attempts": self.service_config.max_retry_attempts,
            "timeout_seconds": self.service_config.timeout_seconds,
            "available_providers": [p.value for p in self.pg_client_manager.factory.get_available_providers()],
            "provider_stats": self._provider_status
        }


# 편의 함수들
def create_payment_service(
    mode: PaymentServiceMode = PaymentServiceMode.MULTI,
    primary_provider: Optional[PGProvider] = None,
    fallback_providers: Optional[List[PGProvider]] = None
) -> PaymentService:
    """결제 서비스 생성 편의 함수"""
    service_config = PaymentServiceConfig(
        mode=mode,
        primary_provider=primary_provider,
        fallback_providers=fallback_providers
    )
    return PaymentService(service_config=service_config)


def create_single_provider_service(provider: PGProvider) -> PaymentService:
    """단일 PG사 서비스 생성 편의 함수"""
    service_config = PaymentServiceConfig(
        mode=PaymentServiceMode.SINGLE,
        primary_provider=provider
    )
    return PaymentService(service_config=service_config)


def create_multi_provider_service(
    primary: PGProvider,
    fallbacks: List[PGProvider]
) -> PaymentService:
    """다중 PG사 폴백 서비스 생성 편의 함수"""
    service_config = PaymentServiceConfig(
        mode=PaymentServiceMode.MULTI,
        primary_provider=primary,
        fallback_providers=fallbacks
    )
    return PaymentService(service_config=service_config)
