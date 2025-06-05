"""
PG 클라이언트 로깅 및 모니터링
"""
import logging
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
from dataclasses import dataclass, field
from collections import defaultdict, deque

from ..models.enums import PGProvider


@dataclass
class RequestMetric:
    """요청 메트릭 정보"""
    provider: PGProvider
    endpoint: str
    method: str
    status_code: int
    response_time: float  # milliseconds
    timestamp: datetime
    success: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ProviderMetrics:
    """PG사별 메트릭"""
    provider: PGProvider
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    recent_requests: deque = field(default_factory=lambda: deque(maxlen=100))
    error_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    @property
    def success_rate(self) -> float:
        """성공률 (0-1)"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def average_response_time(self) -> float:
        """평균 응답 시간 (ms)"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_response_time / self.successful_requests
    
    def add_request(self, metric: RequestMetric):
        """요청 메트릭 추가"""
        self.total_requests += 1
        self.recent_requests.append(metric)
        
        if metric.success:
            self.successful_requests += 1
            self.total_response_time += metric.response_time
        else:
            self.failed_requests += 1
            if metric.error_type:
                self.error_counts[metric.error_type] += 1
    
    def get_recent_success_rate(self, minutes: int = 5) -> float:
        """최근 N분간 성공률"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [
            m for m in self.recent_requests 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return 0.0
        
        successful = sum(1 for m in recent_metrics if m.success)
        return successful / len(recent_metrics)


class PGMetricsCollector:
    """PG 메트릭 수집기"""
    
    def __init__(self):
        self.metrics: Dict[PGProvider, ProviderMetrics] = {}
        self.logger = logging.getLogger("pg_metrics")
    
    def record_request(
        self,
        provider: PGProvider,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        success: bool,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """요청 메트릭 기록"""
        metric = RequestMetric(
            provider=provider,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            timestamp=datetime.now(),
            success=success,
            error_type=error_type,
            error_message=error_message
        )
        
        # PG사별 메트릭이 없으면 생성
        if provider not in self.metrics:
            self.metrics[provider] = ProviderMetrics(provider=provider)
        
        self.metrics[provider].add_request(metric)
        
        # 로그 기록
        log_data = {
            "provider": provider.value,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time_ms": response_time,
            "success": success
        }
        
        if success:
            self.logger.info("PG API 요청 성공", extra=log_data)
        else:
            log_data.update({
                "error_type": error_type,
                "error_message": error_message
            })
            self.logger.error("PG API 요청 실패", extra=log_data)
    
    def get_metrics(self, provider: Optional[PGProvider] = None) -> Dict[str, Any]:
        """메트릭 정보 반환"""
        if provider:
            if provider not in self.metrics:
                return {}
            
            metrics = self.metrics[provider]
            return {
                "provider": provider.value,
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "success_rate": metrics.success_rate,
                "average_response_time_ms": metrics.average_response_time,
                "recent_success_rate_5m": metrics.get_recent_success_rate(5),
                "error_counts": dict(metrics.error_counts)
            }
        
        # 전체 PG사 메트릭
        result = {}
        for provider, metrics in self.metrics.items():
            result[provider.value] = {
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "success_rate": metrics.success_rate,
                "average_response_time_ms": metrics.average_response_time,
                "recent_success_rate_5m": metrics.get_recent_success_rate(5),
                "error_counts": dict(metrics.error_counts)
            }
        
        return result
    
    def reset_metrics(self, provider: Optional[PGProvider] = None):
        """메트릭 초기화"""
        if provider:
            if provider in self.metrics:
                del self.metrics[provider]
        else:
            self.metrics.clear()
    
    def get_health_status(self) -> Dict[str, Any]:
        """헬스 체크 상태 반환"""
        overall_status = "healthy"
        provider_statuses = {}
        
        for provider, metrics in self.metrics.items():
            recent_success_rate = metrics.get_recent_success_rate(5)
            
            if recent_success_rate >= 0.95:
                status = "healthy"
            elif recent_success_rate >= 0.8:
                status = "degraded"
            else:
                status = "unhealthy"
                overall_status = "unhealthy"
            
            provider_statuses[provider.value] = {
                "status": status,
                "recent_success_rate": recent_success_rate,
                "total_requests": metrics.total_requests,
                "average_response_time_ms": metrics.average_response_time
            }
        
        return {
            "overall_status": overall_status,
            "providers": provider_statuses,
            "timestamp": datetime.now().isoformat()
        }


# 전역 메트릭 수집기
_metrics_collector: Optional[PGMetricsCollector] = None


def get_metrics_collector() -> PGMetricsCollector:
    """전역 메트릭 수집기 반환"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = PGMetricsCollector()
    return _metrics_collector


def set_metrics_collector(collector: PGMetricsCollector):
    """전역 메트릭 수집기 설정 (테스트용)"""
    global _metrics_collector
    _metrics_collector = collector


def monitor_pg_request(func: Callable) -> Callable:
    """PG 요청 모니터링 데코레이터"""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        start_time = time.time()
        provider = getattr(self, 'provider', None)
        endpoint = args[0] if args else 'unknown'
        method = func.__name__.upper()
        
        try:
            result = await func(self, *args, **kwargs)
            
            # 성공 메트릭 기록
            response_time = (time.time() - start_time) * 1000
            status_code = result[0] if isinstance(result, tuple) else 200
            
            collector = get_metrics_collector()
            collector.record_request(
                provider=provider,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time=response_time,
                success=True
            )
            
            return result
            
        except Exception as e:
            # 실패 메트릭 기록
            response_time = (time.time() - start_time) * 1000
            error_type = type(e).__name__
            error_message = str(e)
            
            collector = get_metrics_collector()
            collector.record_request(
                provider=provider,
                endpoint=endpoint,
                method=method,
                status_code=getattr(e, 'status_code', 500),
                response_time=response_time,
                success=False,
                error_type=error_type,
                error_message=error_message
            )
            
            raise
    
    return wrapper


class PGLogger:
    """PG 전용 로거"""
    
    def __init__(self, provider: PGProvider):
        self.provider = provider
        self.logger = logging.getLogger(f"pg_client.{provider.value}")
    
    def log_request(self, method: str, endpoint: str, data: Optional[Dict] = None):
        """요청 로그"""
        self.logger.debug(
            f"PG API 요청: {method} {endpoint}",
            extra={
                "provider": self.provider.value,
                "method": method,
                "endpoint": endpoint,
                "has_data": bool(data)
            }
        )
    
    def log_response(self, status_code: int, response_time: float, success: bool):
        """응답 로그"""
        level = logging.INFO if success else logging.ERROR
        self.logger.log(
            level,
            f"PG API 응답: {status_code} ({response_time:.2f}ms)",
            extra={
                "provider": self.provider.value,
                "status_code": status_code,
                "response_time_ms": response_time,
                "success": success
            }
        )
    
    def log_error(self, error: Exception, context: Optional[Dict] = None):
        """에러 로그"""
        self.logger.error(
            f"PG API 오류: {error}",
            extra={
                "provider": self.provider.value,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {}
            },
            exc_info=True
        )


def setup_pg_logging(level: int = logging.INFO):
    """PG 로깅 설정"""
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # PG 클라이언트 로거 설정
    pg_logger = logging.getLogger("pg_client")
    pg_logger.setLevel(level)
    
    if not pg_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        pg_logger.addHandler(handler)
    
    # 메트릭 로거 설정
    metrics_logger = logging.getLogger("pg_metrics")
    metrics_logger.setLevel(level)
    
    if not metrics_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        metrics_logger.addHandler(handler)
