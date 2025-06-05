"""
PG 클라이언트 팩토리
"""
from typing import Dict, Type, Optional
from ..models.enums import PGProvider
from ..config import Config, PGConfig, get_config
from .base import BasePGClient
from .kg_inicis import KGInicisClient
from .exceptions import PGConfigurationException


class PGClientFactory:
    """PG 클라이언트 팩토리 클래스"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self._client_registry: Dict[PGProvider, Type[BasePGClient]] = {}
        self._client_instances: Dict[PGProvider, BasePGClient] = {}
        
        # 기본 클라이언트 자동 등록
        self._register_default_clients()
    
    def register_client(self, provider: PGProvider, client_class: Type[BasePGClient]):
        """PG사 클라이언트 클래스 등록"""
        if not issubclass(client_class, BasePGClient):
            raise ValueError(f"클라이언트 클래스는 BasePGClient를 상속받아야 합니다: {client_class}")
        
        self._client_registry[provider] = client_class
    
    def _register_default_clients(self):
        """기본 클라이언트들 자동 등록"""
        self.register_client(PGProvider.KG_INICIS, KGInicisClient)
    
    def create_client(self, provider: PGProvider) -> BasePGClient:
        """PG사 클라이언트 인스턴스 생성"""
        # 이미 생성된 인스턴스가 있으면 반환 (싱글톤 패턴)
        if provider in self._client_instances:
            return self._client_instances[provider]
        
        # 설정 확인
        pg_config = self.config.get_pg_config(provider)
        if not pg_config:
            raise PGConfigurationException(
                f"PG사 설정이 없습니다: {provider.value}",
                provider=provider
            )
        
        # 클라이언트 클래스 확인
        if provider not in self._client_registry:
            raise PGConfigurationException(
                f"등록된 클라이언트가 없습니다: {provider.value}",
                provider=provider
            )
        
        # 클라이언트 인스턴스 생성
        client_class = self._client_registry[provider]
        client_instance = client_class(pg_config, provider)
        
        # 인스턴스 캐시
        self._client_instances[provider] = client_instance
        
        return client_instance
    
    def get_client(self, provider: PGProvider) -> Optional[BasePGClient]:
        """기존 클라이언트 인스턴스 반환 (없으면 None)"""
        return self._client_instances.get(provider)
    
    def get_available_providers(self) -> list[PGProvider]:
        """사용 가능한 PG사 목록 반환"""
        return [
            provider for provider in self.config.get_configured_providers()
            if provider in self._client_registry
        ]
    
    def is_provider_available(self, provider: PGProvider) -> bool:
        """특정 PG사가 사용 가능한지 확인"""
        return (
            self.config.is_configured(provider) and 
            provider in self._client_registry
        )
    
    async def close_all(self):
        """모든 클라이언트 인스턴스 종료"""
        for client in self._client_instances.values():
            await client.close()
        self._client_instances.clear()
    
    def clear_cache(self):
        """클라이언트 인스턴스 캐시 정리 (비동기 종료 없이)"""
        self._client_instances.clear()


# 전역 팩토리 인스턴스
_factory_instance: Optional[PGClientFactory] = None


def get_pg_client_factory() -> PGClientFactory:
    """전역 PG 클라이언트 팩토리 반환"""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = PGClientFactory()
    return _factory_instance


def set_pg_client_factory(factory: PGClientFactory):
    """전역 PG 클라이언트 팩토리 설정 (테스트용)"""
    global _factory_instance
    _factory_instance = factory


class PGClientManager:
    """PG 클라이언트 관리자 - 고수준 인터페이스"""
    
    def __init__(self, factory: Optional[PGClientFactory] = None):
        self.factory = factory or get_pg_client_factory()
    
    async def get_client(self, provider: PGProvider) -> BasePGClient:
        """PG사 클라이언트 반환"""
        return self.factory.create_client(provider)
    
    async def get_best_available_client(
        self, 
        preferred_providers: Optional[list[PGProvider]] = None
    ) -> BasePGClient:
        """가장 적합한 클라이언트 반환"""
        available_providers = self.factory.get_available_providers()
        
        if not available_providers:
            raise PGConfigurationException("사용 가능한 PG사가 없습니다")
        
        # 선호 순서가 있으면 해당 순서로 반환
        if preferred_providers:
            for provider in preferred_providers:
                if provider in available_providers:
                    return await self.get_client(provider)
        
        # 선호 순서가 없으면 첫 번째 사용 가능한 PG사 반환
        return await self.get_client(available_providers[0])
    
    async def execute_with_fallback(
        self,
        operation_func,
        providers: Optional[list[PGProvider]] = None,
        *args,
        **kwargs
    ):
        """폴백 로직으로 작업 실행"""
        target_providers = providers or self.factory.get_available_providers()
        
        if not target_providers:
            raise PGConfigurationException("사용 가능한 PG사가 없습니다")
        
        last_exception = None
        
        for provider in target_providers:
            try:
                client = await self.get_client(provider)
                return await operation_func(client, *args, **kwargs)
                
            except Exception as e:
                last_exception = e
                # 다음 PG사로 계속 시도
                continue
        
        # 모든 PG사에서 실패
        raise last_exception
    
    async def close_all(self):
        """모든 클라이언트 종료"""
        await self.factory.close_all()
    
    def get_status(self) -> Dict[str, Dict[str, any]]:
        """PG사별 상태 정보 반환"""
        status = {}
        
        for provider in PGProvider:
            status[provider.value] = {
                "configured": self.factory.config.is_configured(provider),
                "registered": provider in self.factory._client_registry,
                "available": self.factory.is_provider_available(provider),
                "instance_cached": provider in self.factory._client_instances
            }
        
        return status


# 편의 함수들
async def get_pg_client(provider: PGProvider) -> BasePGClient:
    """PG사 클라이언트 반환 (편의 함수)"""
    manager = PGClientManager()
    return await manager.get_client(provider)


async def get_available_client() -> BasePGClient:
    """사용 가능한 첫 번째 클라이언트 반환 (편의 함수)"""
    manager = PGClientManager()
    return await manager.get_best_available_client()
