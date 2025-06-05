"""
결제 시스템 환경설정 관리
"""
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from .models.enums import PGProvider


class Environment(str, Enum):
    """환경 타입"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class PGConfig:
    """PG사별 설정 정보"""
    merchant_id: str
    api_key: str
    secret_key: Optional[str] = None
    api_base_url: str = ""
    is_production: bool = False
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # 웹훅 설정
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    
    # 추가 설정
    extra_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_config is None:
            self.extra_config = {}


class Config:
    """통합 환경설정 관리 클래스"""
    
    def __init__(self, env: Environment = Environment.DEVELOPMENT):
        self.env = env
        self.pg_configs: Dict[PGProvider, PGConfig] = {}
        self._load_config()
    
    def _load_config(self):
        """환경변수 또는 설정 파일에서 설정 로드"""
        # KG이니시스 설정
        kg_config = self._load_pg_config(PGProvider.KG_INICIS)
        if kg_config:
            self.pg_configs[PGProvider.KG_INICIS] = kg_config
        

        
        # 네이버페이 설정
        naver_config = self._load_pg_config(PGProvider.NAVER_PAY)
        if naver_config:
            self.pg_configs[PGProvider.NAVER_PAY] = naver_config
        
        # 카카오페이 설정
        kakao_config = self._load_pg_config(PGProvider.KAKAO_PAY)
        if kakao_config:
            self.pg_configs[PGProvider.KAKAO_PAY] = kakao_config
        
        # 나이스페이먼츠 설정
        nice_config = self._load_pg_config(PGProvider.NICE_PAYMENTS)
        if nice_config:
            self.pg_configs[PGProvider.NICE_PAYMENTS] = nice_config
    
    def _load_pg_config(self, provider: PGProvider) -> Optional[PGConfig]:
        """특정 PG사 설정 로드"""
        prefix = provider.value.upper()
        
        merchant_id = os.getenv(f"{prefix}_MERCHANT_ID")
        api_key = os.getenv(f"{prefix}_API_KEY")
        
        if not merchant_id or not api_key:
            return None
        
        return PGConfig(
            merchant_id=merchant_id,
            api_key=api_key,
            secret_key=os.getenv(f"{prefix}_SECRET_KEY"),
            api_base_url=self._get_api_base_url(provider),
            is_production=self.env == Environment.PRODUCTION,
            timeout=int(os.getenv(f"{prefix}_TIMEOUT", "30")),
            max_retries=int(os.getenv(f"{prefix}_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv(f"{prefix}_RETRY_DELAY", "1.0")),
            webhook_url=os.getenv(f"{prefix}_WEBHOOK_URL"),
            webhook_secret=os.getenv(f"{prefix}_WEBHOOK_SECRET"),
        )
    
    def _get_api_base_url(self, provider: PGProvider) -> str:
        """PG사별 API 기본 URL 반환"""
        urls = {
            PGProvider.KG_INICIS: {
                Environment.PRODUCTION: "https://stgstdpay.inicis.com",
                Environment.STAGING: "https://stgstdpay.inicis.com", 
                Environment.DEVELOPMENT: "https://stgstdpay.inicis.com"
            },

            PGProvider.NAVER_PAY: {
                Environment.PRODUCTION: "https://dev.apis.naver.com/naverpay-partner/naverpay",
                Environment.STAGING: "https://dev.apis.naver.com/naverpay-partner/naverpay",
                Environment.DEVELOPMENT: "https://dev.apis.naver.com/naverpay-partner/naverpay"
            },
            PGProvider.KAKAO_PAY: {
                Environment.PRODUCTION: "https://kapi.kakao.com",
                Environment.STAGING: "https://kapi.kakao.com",
                Environment.DEVELOPMENT: "https://kapi.kakao.com"
            },
            PGProvider.NICE_PAYMENTS: {
                Environment.PRODUCTION: "https://webapi.nicepay.co.kr",
                Environment.STAGING: "https://sandbox-api.nicepay.co.kr",
                Environment.DEVELOPMENT: "https://sandbox-api.nicepay.co.kr"
            }
        }
        
        provider_urls = urls.get(provider, {})
        return provider_urls.get(self.env, "")
    
    def get_pg_config(self, provider: PGProvider) -> Optional[PGConfig]:
        """특정 PG사 설정 반환"""
        return self.pg_configs.get(provider)
    
    def add_pg_config(self, provider: PGProvider, config: PGConfig):
        """PG사 설정 추가"""
        self.pg_configs[provider] = config
    
    def is_configured(self, provider: PGProvider) -> bool:
        """특정 PG사가 설정되었는지 확인"""
        return provider in self.pg_configs
    
    def get_configured_providers(self) -> list[PGProvider]:
        """설정된 PG사 목록 반환"""
        return list(self.pg_configs.keys())
    
    @property
    def is_production(self) -> bool:
        """운영 환경 여부"""
        return self.env == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """개발 환경 여부"""
        return self.env == Environment.DEVELOPMENT


# 전역 설정 인스턴스
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """전역 설정 인스턴스 반환"""
    global _config_instance
    if _config_instance is None:
        env_name = os.getenv("ENVIRONMENT", "development")
        try:
            env = Environment(env_name.lower())
        except ValueError:
            env = Environment.DEVELOPMENT
        _config_instance = Config(env)
    return _config_instance


def set_config(config: Config):
    """전역 설정 인스턴스 설정 (테스트용)"""
    global _config_instance
    _config_instance = config
