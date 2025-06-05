"""
결제 워크플로우 관리

결제 플로우의 상태를 추적하고 관리하는 모듈입니다.
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

from ..models.enums import PaymentStatus, PGProvider
from ..models.exceptions import PaymentException


logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """워크플로우 상태"""
    PENDING = "pending"        # 대기 중
    PROCESSING = "processing"  # 처리 중
    SUCCESS = "success"        # 성공
    FAILED = "failed"          # 실패
    CANCELLED = "cancelled"    # 취소됨
    TIMEOUT = "timeout"        # 시간 초과


class WorkflowStepType(Enum):
    """워크플로우 단계 타입"""
    VALIDATION = "validation"    # 검증
    PAYMENT = "payment"          # 결제 처리
    NOTIFICATION = "notification"  # 알림
    LOGGING = "logging"          # 로깅
    CLEANUP = "cleanup"          # 정리


@dataclass
class WorkflowStep:
    """워크플로우 단계"""
    name: str
    step_type: WorkflowStepType
    function: Callable
    required: bool = True
    timeout_seconds: float = 30.0
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class WorkflowExecution:
    """워크플로우 실행 정보"""
    workflow_id: str
    order_id: str
    provider: Optional[PGProvider] = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    current_step: Optional[str] = None
    steps_completed: List[str] = field(default_factory=list)
    steps_failed: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def duration(self) -> Optional[timedelta]:
        """실행 시간 계산"""
        if self.completed_at:
            return self.completed_at - self.started_at
        return datetime.now() - self.started_at


class PaymentWorkflow:
    """
    결제 워크플로우
    
    결제 처리의 각 단계를 정의하고 실행을 관리합니다.
    """
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.steps: List[WorkflowStep] = []
        self.executions: Dict[str, WorkflowExecution] = {}
        
    def add_step(self, step: WorkflowStep):
        """워크플로우 단계 추가"""
        self.steps.append(step)
        logger.debug(f"워크플로우 단계 추가: {step.name}")
    
    async def execute(
        self, 
        order_id: str, 
        context: Dict[str, Any],
        provider: Optional[PGProvider] = None
    ) -> WorkflowExecution:
        """워크플로우 실행"""
        execution_id = f"{self.workflow_id}_{order_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        execution = WorkflowExecution(
            workflow_id=self.workflow_id,
            order_id=order_id,
            provider=provider
        )
        
        self.executions[execution_id] = execution
        execution.status = WorkflowStatus.PROCESSING
        
        logger.info(f"워크플로우 실행 시작: {execution_id}")
        
        try:
            for step in self.steps:
                execution.current_step = step.name
                logger.debug(f"단계 실행: {step.name}")
                
                try:
                    # 단계 실행 (재시도 로직 포함)
                    await self._execute_step_with_retry(step, context)
                    execution.steps_completed.append(step.name)
                    
                except Exception as e:
                    execution.steps_failed.append(step.name)
                    execution.error_message = str(e)
                    
                    logger.error(f"단계 실행 실패: {step.name}, 오류: {str(e)}")
                    
                    # 필수 단계 실패 시 워크플로우 중단
                    if step.required:
                        execution.status = WorkflowStatus.FAILED
                        raise PaymentException(f"필수 단계 실패: {step.name}") from e
                    
                    # 선택적 단계는 계속 진행
                    logger.warning(f"선택적 단계 실패 (계속 진행): {step.name}")
            
            # 모든 단계 완료
            execution.status = WorkflowStatus.SUCCESS
            execution.completed_at = datetime.now()
            
            logger.info(f"워크플로우 실행 완료: {execution_id}")
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.completed_at = datetime.now()
            execution.error_message = str(e)
            
            logger.error(f"워크플로우 실행 실패: {execution_id}, 오류: {str(e)}")
            raise
        
        return execution
    
    async def _execute_step_with_retry(self, step: WorkflowStep, context: Dict[str, Any]):
        """재시도 로직을 포함한 단계 실행"""
        last_exception = None
        
        for attempt in range(step.max_retries + 1):
            try:
                # 타임아웃 설정
                await asyncio.wait_for(
                    step.function(context),
                    timeout=step.timeout_seconds
                )
                return  # 성공 시 반환
                
            except asyncio.TimeoutError:
                last_exception = PaymentException(f"단계 시간 초과: {step.name}")
            except Exception as e:
                last_exception = e
            
            # 재시도 전 대기 (마지막 시도가 아닌 경우)
            if attempt < step.max_retries:
                await asyncio.sleep(step.retry_delay)
                logger.warning(f"단계 재시도: {step.name} (시도 {attempt + 2}/{step.max_retries + 1})")
        
        # 모든 재시도 실패
        raise PaymentException(f"단계 재시도 후에도 실패: {step.name}") from last_exception
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """실행 정보 조회"""
        return self.executions.get(execution_id)
    
    def get_executions_by_order(self, order_id: str) -> List[WorkflowExecution]:
        """주문번호로 실행 정보 조회"""
        return [
            execution for execution in self.executions.values()
            if execution.order_id == order_id
        ]
    
    def cleanup_old_executions(self, max_age_hours: int = 24):
        """오래된 실행 정보 정리"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        old_executions = [
            execution_id for execution_id, execution in self.executions.items()
            if execution.started_at < cutoff_time
        ]
        
        for execution_id in old_executions:
            del self.executions[execution_id]
        
        logger.info(f"오래된 실행 정보 정리: {len(old_executions)}개")


class StandardPaymentWorkflow(PaymentWorkflow):
    """표준 결제 워크플로우"""
    
    def __init__(self):
        super().__init__("standard_payment")
        self._setup_standard_steps()
    
    def _setup_standard_steps(self):
        """표준 결제 단계 설정"""
        
        # 1. 요청 검증
        self.add_step(WorkflowStep(
            name="validate_request",
            step_type=WorkflowStepType.VALIDATION,
            function=self._validate_request,
            required=True,
            timeout_seconds=5.0
        ))
        
        # 2. 결제 전 로깅
        self.add_step(WorkflowStep(
            name="log_payment_start",
            step_type=WorkflowStepType.LOGGING,
            function=self._log_payment_start,
            required=False,
            timeout_seconds=5.0
        ))
        
        # 3. 결제 처리
        self.add_step(WorkflowStep(
            name="process_payment",
            step_type=WorkflowStepType.PAYMENT,
            function=self._process_payment,
            required=True,
            timeout_seconds=60.0,
            max_retries=2
        ))
        
        # 4. 결제 후 알림
        self.add_step(WorkflowStep(
            name="send_notification",
            step_type=WorkflowStepType.NOTIFICATION,
            function=self._send_notification,
            required=False,
            timeout_seconds=10.0
        ))
        
        # 5. 결제 완료 로깅
        self.add_step(WorkflowStep(
            name="log_payment_complete",
            step_type=WorkflowStepType.LOGGING,
            function=self._log_payment_complete,
            required=False,
            timeout_seconds=5.0
        ))
    
    async def _validate_request(self, context: Dict[str, Any]):
        """요청 검증"""
        request = context.get("request")
        if not request:
            raise PaymentException("결제 요청이 없습니다")
        
        # 여기에 추가 검증 로직 구현
        logger.debug("결제 요청 검증 완료")
    
    async def _log_payment_start(self, context: Dict[str, Any]):
        """결제 시작 로깅"""
        request = context.get("request")
        logger.info(f"결제 처리 시작 - 주문번호: {request.order_id}, 금액: {request.amount}")
    
    async def _process_payment(self, context: Dict[str, Any]):
        """결제 처리"""
        payment_service = context.get("payment_service")
        request = context.get("request")
        
        if not payment_service or not request:
            raise PaymentException("결제 서비스 또는 요청이 없습니다")
        
        # 실제 결제 처리
        response = await payment_service.process_payment(request)
        context["response"] = response
        
        logger.info(f"결제 처리 완료 - 주문번호: {request.order_id}")
    
    async def _send_notification(self, context: Dict[str, Any]):
        """알림 발송"""
        response = context.get("response")
        if response:
            # 여기에 알림 발송 로직 구현 (예: 이메일, SMS, 웹훅 등)
            logger.debug(f"결제 완료 알림 발송 - 주문번호: {response.order_id}")
    
    async def _log_payment_complete(self, context: Dict[str, Any]):
        """결제 완료 로깅"""
        response = context.get("response")
        if response:
            logger.info(f"결제 플로우 완료 - 주문번호: {response.order_id}, 상태: {response.status}")


class WorkflowManager:
    """워크플로우 관리자"""
    
    def __init__(self):
        self.workflows: Dict[str, PaymentWorkflow] = {}
        self._register_default_workflows()
    
    def _register_default_workflows(self):
        """기본 워크플로우 등록"""
        self.register_workflow(StandardPaymentWorkflow())
    
    def register_workflow(self, workflow: PaymentWorkflow):
        """워크플로우 등록"""
        self.workflows[workflow.workflow_id] = workflow
        logger.info(f"워크플로우 등록: {workflow.workflow_id}")
    
    def get_workflow(self, workflow_id: str) -> Optional[PaymentWorkflow]:
        """워크플로우 조회"""
        return self.workflows.get(workflow_id)
    
    async def execute_workflow(
        self,
        workflow_id: str,
        order_id: str,
        context: Dict[str, Any],
        provider: Optional[PGProvider] = None
    ) -> WorkflowExecution:
        """워크플로우 실행"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise PaymentException(f"워크플로우를 찾을 수 없습니다: {workflow_id}")
        
        return await workflow.execute(order_id, context, provider)
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """워크플로우 상태 조회"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return {"error": "워크플로우를 찾을 수 없습니다"}
        
        return {
            "workflow_id": workflow_id,
            "total_executions": len(workflow.executions),
            "recent_executions": list(workflow.executions.keys())[-10:],  # 최근 10개
            "steps": [
                {
                    "name": step.name,
                    "type": step.step_type.value,
                    "required": step.required,
                    "timeout": step.timeout_seconds
                }
                for step in workflow.steps
            ]
        }
    
    def cleanup_all_workflows(self, max_age_hours: int = 24):
        """모든 워크플로우의 오래된 실행 정보 정리"""
        for workflow in self.workflows.values():
            workflow.cleanup_old_executions(max_age_hours)


# 전역 워크플로우 관리자
_workflow_manager: Optional[WorkflowManager] = None


def get_workflow_manager() -> WorkflowManager:
    """전역 워크플로우 관리자 반환"""
    global _workflow_manager
    if _workflow_manager is None:
        _workflow_manager = WorkflowManager()
    return _workflow_manager


def set_workflow_manager(manager: WorkflowManager):
    """전역 워크플로우 관리자 설정 (테스트용)"""
    global _workflow_manager
    _workflow_manager = manager
