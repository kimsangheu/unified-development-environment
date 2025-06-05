"""
PG 핸들러 패키지

이 패키지는 각 PG사와의 API 통신을 담당하는 클라이언트들을 포함합니다.
"""

# 기본 클래스 import
from .base import BasePGClient
from .kg_inicis import KGInicisClient

# 예외 클래스 import
from .exceptions import (
    PGClientException,
    PGHttpException,
    PGConnectionException,
    PGTimeoutException,
    PGAuthenticationException,
    PGConfigurationException,
    PGRateLimitException,
    PGValidationException,
    PGResponseException,
    PGRetryExhaustedException
)

# 팩토리 및 관리자 import
from .factory import (
    PGClientFactory,
    PGClientManager,
    get_pg_client_factory,
    set_pg_client_factory,
    get_pg_client,
    get_available_client
)

# 모니터링 import
from .monitoring import (
    RequestMetric,
    ProviderMetrics,
    PGMetricsCollector,
    PGLogger,
    get_metrics_collector,
    set_metrics_collector,
    monitor_pg_request,
    setup_pg_logging
)

__all__ = [
    # 기본 클래스
    "BasePGClient",
    "KGInicisClient",
    
    # 예외 클래스
    "PGClientException",
    "PGHttpException",
    "PGConnectionException",
    "PGTimeoutException",
    "PGAuthenticationException",
    "PGConfigurationException",
    "PGRateLimitException",
    "PGValidationException",
    "PGResponseException",
    "PGRetryExhaustedException",
    
    # 팩토리 및 관리자
    "PGClientFactory",
    "PGClientManager",
    "get_pg_client_factory",
    "set_pg_client_factory",
    "get_pg_client",
    "get_available_client",
    
    # 모니터링
    "RequestMetric",
    "ProviderMetrics",
    "PGMetricsCollector",
    "PGLogger",
    "get_metrics_collector",
    "set_metrics_collector",
    "monitor_pg_request",
    "setup_pg_logging"
]

# 패키지 버전
__version__ = "1.0.0"
