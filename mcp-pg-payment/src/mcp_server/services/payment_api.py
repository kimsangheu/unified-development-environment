"""
통합 결제 API 파사드

클라이언트가 사용할 수 있는 통합 결제 인터페이스를 제공합니다.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .payment_service import PaymentService, PaymentServiceConfig, PaymentServiceMode
from .workflow import WorkflowManager, get_workflow_manager
from ..models.requests import PaymentRequest, PaymentCancelRequest, PaymentStatusRequest
from ..models.responses import PaymentResponse, PaymentCancelResponse, PaymentStatusResponse
from ..models.enums import PGProvider
from ..models.exceptions import PaymentException, PaymentValidationException
from ..config import Config, get_config


logger = logging.getLogger(__name__)


class PaymentAPI:
    """
    통합 결제 API
    
    외부에서 사용할 수 있는 통합 결제 인터페이스를 제공합니다.
    PaymentService와 WorkflowManager를 조합하여 완전한 결제 솔루션을 제공합니다.
    """
    
    def __init__(
        self,
        config: Optional[Config] = None,
        service_config: Optional[PaymentServiceConfig] = None,
        workflow_manager: Optional[WorkflowManager] = None
    ):
        self.config = config or get_config()
        self.payment_service = PaymentService(config, service_config)
        self.workflow_manager = workflow_manager or get_workflow_manager()
        
        logger.info("PaymentAPI 초기화 완료")
    
    async def process_payment(
        self, 
        request: PaymentRequest,
        preferred_provider: Optional[PGProvider] = None,
        use_workflow: bool = True
    ) -> PaymentResponse:
        """
        결제 처리
        
        Args:
            request: 결제 요청 정보
            preferred_provider: 선호하는 PG사
            use_workflow: 워크플로우 사용 여부
            
        Returns:
            PaymentResponse: 결제 처리 결과
        """
        if use_workflow:
            return await self._process_payment_with_workflow(request, preferred_provider)
        else:
            return await self.payment_service.process_payment(request, preferred_provider)
    
    async def _process_payment_with_workflow(
        self,
        request: PaymentRequest,
        preferred_provider: Optional[PGProvider] = None
    ) -> PaymentResponse:
        """워크플로우를 사용한 결제 처리"""
        context = {
            "request": request,
            "payment_service": self.payment_service,
            "preferred_provider": preferred_provider
        }
        
        execution = await self.workflow_manager.execute_workflow(
            workflow_id="standard_payment",
            order_id=request.order_id,
            context=context,
            provider=preferred_provider
        )
        
        response = context.get("response")
        if not response:
            raise PaymentException("워크플로우에서 결제 응답을 생성하지 못했습니다")
        
        # 워크플로우 실행 정보를 응답에 추가
        response.workflow_execution_id = f"{execution.workflow_id}_{execution.order_id}_{execution.started_at.strftime('%Y%m%d%H%M%S')}"
        
        return response
    
    async def get_payment_status(
        self, 
        request: PaymentStatusRequest,
        provider: Optional[PGProvider] = None
    ) -> PaymentStatusResponse:
        """
        결제 상태 조회
        
        Args:
            request: 결제 상태 조회 요청
            provider: 특정 PG사 지정
            
        Returns:
            PaymentStatusResponse: 결제 상태 조회 결과
        """
        return await self.payment_service.get_payment_status(request, provider)
    
    async def cancel_payment(
        self, 
        request: PaymentCancelRequest,
        provider: Optional[PGProvider] = None
    ) -> PaymentCancelResponse:
        """
        결제 취소
        
        Args:
            request: 결제 취소 요청
            provider: 특정 PG사 지정
            
        Returns:
            PaymentCancelResponse: 결제 취소 결과
        """
        return await self.payment_service.cancel_payment(request, provider)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        시스템 상태 확인
        
        Returns:
            Dict: 시스템 상태 정보
        """
        service_health = await self.payment_service.health_check()
        
        # 워크플로우 상태 추가
        workflow_health = {}
        for workflow_id in self.workflow_manager.workflows.keys():
            workflow_health[workflow_id] = self.workflow_manager.get_workflow_status(workflow_id)
        
        return {
            **service_health,
            "workflows": workflow_health,
            "api": {
                "status": "healthy",
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def get_supported_providers(self) -> List[Dict[str, Any]]:
        """
        지원하는 PG사 목록 조회
        
        Returns:
            List: PG사 정보 목록
        """
        providers_info = []
        
        for provider in PGProvider:
            info = {
                "provider": provider.value,
                "name": self._get_provider_display_name(provider),
                "configured": self.config.is_configured(provider),
                "available": self.payment_service.pg_client_manager.factory.is_provider_available(provider)
            }
            providers_info.append(info)
        
        return providers_info
    
    def _get_provider_display_name(self, provider: PGProvider) -> str:
        """PG사 표시 이름 반환"""
        names = {
            PGProvider.KG_INICIS: "KG이니시스",
            PGProvider.TOSS_PAYMENTS: "토스페이먼츠",
            PGProvider.NICE_PAYMENTS: "나이스페이",
            PGProvider.PORTONE: "포트원",
            PGProvider.KAKAO_PAY: "카카오페이",
            PGProvider.NAVER_PAY: "네이버페이"
        }
        return names.get(provider, provider.value)
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        서비스 정보 조회
        
        Returns:
            Dict: 서비스 정보
        """
        return {
            "api_version": "1.0.0",
            "service_info": self.payment_service.get_service_info(),
            "supported_providers": self.get_supported_providers(),
            "workflow_info": {
                "available_workflows": list(self.workflow_manager.workflows.keys()),
                "default_workflow": "standard_payment"
            }
        }
    
    async def batch_process_payments(
        self,
        requests: List[PaymentRequest],
        preferred_provider: Optional[PGProvider] = None,
        max_concurrent: int = 5
    ) -> List[PaymentResponse]:
        """
        배치 결제 처리
        
        Args:
            requests: 결제 요청 목록
            preferred_provider: 선호하는 PG사
            max_concurrent: 최대 동시 처리 수
            
        Returns:
            List[PaymentResponse]: 결제 처리 결과 목록
        """
        import asyncio
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_payment(request: PaymentRequest):
            async with semaphore:
                try:
                    return await self.process_payment(request, preferred_provider)
                except Exception as e:
                    # 개별 결제 실패 시 오류 응답 생성
                    return PaymentResponse(
                        order_id=request.order_id,
                        status="FAILED",
                        message=f"결제 처리 실패: {str(e)}",
                        amount=request.amount
                    )
        
        tasks = [process_single_payment(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 발생한 경우 오류 응답으로 변환
        result = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                result.append(PaymentResponse(
                    order_id=requests[i].order_id,
                    status="FAILED",
                    message=f"배치 처리 오류: {str(response)}",
                    amount=requests[i].amount
                ))
            else:
                result.append(response)
        
        return result
    
    async def get_payment_history(
        self,
        order_id: Optional[str] = None,
        provider: Optional[PGProvider] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        결제 이력 조회
        
        Args:
            order_id: 주문번호 (옵션)
            provider: PG사 (옵션)
            start_date: 시작 일시 (옵션)
            end_date: 종료 일시 (옵션)
            limit: 최대 조회 수
            
        Returns:
            List: 결제 이력 목록
        """
        # 실제 구현에서는 데이터베이스나 로그에서 이력을 조회해야 함
        # 여기서는 워크플로우 실행 이력을 기반으로 간단히 구현
        
        history = []
        
        for workflow in self.workflow_manager.workflows.values():
            for execution in workflow.executions.values():
                # 필터링 조건 적용
                if order_id and execution.order_id != order_id:
                    continue
                
                if provider and execution.provider != provider:
                    continue
                
                if start_date and execution.started_at < start_date:
                    continue
                
                if end_date and execution.started_at > end_date:
                    continue
                
                history.append({
                    "order_id": execution.order_id,
                    "provider": execution.provider.value if execution.provider else None,
                    "status": execution.status.value,
                    "started_at": execution.started_at.isoformat(),
                    "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                    "duration_seconds": execution.duration().total_seconds() if execution.duration() else None,
                    "steps_completed": execution.steps_completed,
                    "steps_failed": execution.steps_failed,
                    "error_message": execution.error_message
                })
        
        # 최신 순으로 정렬하고 제한
        history.sort(key=lambda x: x["started_at"], reverse=True)
        return history[:limit]
    
    async def close(self):
        """API 종료 및 리소스 정리"""
        logger.info("PaymentAPI 종료")
        await self.payment_service.close()
        
        # 워크플로우 정리
        self.workflow_manager.cleanup_all_workflows()


# 편의 함수들
def create_payment_api(
    mode: PaymentServiceMode = PaymentServiceMode.MULTI,
    primary_provider: Optional[PGProvider] = None,
    fallback_providers: Optional[List[PGProvider]] = None
) -> PaymentAPI:
    """결제 API 생성 편의 함수"""
    service_config = PaymentServiceConfig(
        mode=mode,
        primary_provider=primary_provider,
        fallback_providers=fallback_providers
    )
    return PaymentAPI(service_config=service_config)


def create_single_provider_api(provider: PGProvider) -> PaymentAPI:
    """단일 PG사 API 생성 편의 함수"""
    service_config = PaymentServiceConfig(
        mode=PaymentServiceMode.SINGLE,
        primary_provider=provider
    )
    return PaymentAPI(service_config=service_config)


def create_multi_provider_api(
    primary: PGProvider,
    fallbacks: List[PGProvider]
) -> PaymentAPI:
    """다중 PG사 폴백 API 생성 편의 함수"""
    service_config = PaymentServiceConfig(
        mode=PaymentServiceMode.MULTI,
        primary_provider=primary,
        fallback_providers=fallbacks
    )
    return PaymentAPI(service_config=service_config)


# 전역 API 인스턴스
_payment_api: Optional[PaymentAPI] = None


def get_payment_api() -> PaymentAPI:
    """전역 결제 API 반환"""
    global _payment_api
    if _payment_api is None:
        _payment_api = PaymentAPI()
    return _payment_api


def set_payment_api(api: PaymentAPI):
    """전역 결제 API 설정 (테스트용)"""
    global _payment_api
    _payment_api = api
