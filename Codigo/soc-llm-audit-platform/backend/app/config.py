"""
SOC-LLM Audit Platform - Application Configuration
Configuración centralizada con variables de entorno.
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, List
from functools import lru_cache
import json as _json


def _parse_list(v):
    """Parse a list from env var: supports JSON array or comma-separated string."""
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        v = v.strip()
        if v.startswith("["):
            return _json.loads(v)
        return [i.strip() for i in v.split(",") if i.strip()]
    return v


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "SOC-LLM Audit Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-me-in-production-with-secure-random-key"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://soc_user:soc_password@localhost:5432/soc_llm_audit"
    DATABASE_SYNC_URL: str = "postgresql://soc_user:soc_password@localhost:5432/soc_llm_audit"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_SESSION_DB: int = 1
    REDIS_RATE_LIMIT_DB: int = 2

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_GROUP_ID: str = "soc-llm-audit"
    KAFKA_TOPICS_RAW: str = "siem.alerts.raw"
    KAFKA_TOPICS_ANONYMIZED: str = "siem.alerts.anonymized"
    KAFKA_TOPICS_PII: str = "compliance.audit.pii"
    KAFKA_TOPICS_BLOCKED: str = "compliance.blocked.alerts"

    # Auth / JWT
    JWT_SECRET_KEY: str = "jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # RBAC Roles
    ROLES: str = "analyst_t1,analyst_t2,soc_lead,dpo,ciso,auditor"

    # LLM Configuration
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4"
    LLM_API_KEY: Optional[str] = None
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.1
    LLM_TIMEOUT: int = 30
    LLM_RATE_LIMIT_RPM: int = 60

    # PII Scanner
    PII_CONFIDENCE_THRESHOLD: float = 0.7
    PII_SUPPORTED_LANGUAGES: str = "es,en"

    # Compliance Scoring Weights (sum = 1.0)
    CS_WEIGHT_DATA_MINIMIZATION: float = 0.15
    CS_WEIGHT_LEGAL_BASIS: float = 0.15
    CS_WEIGHT_TRANSPARENCY: float = 0.15
    CS_WEIGHT_PIPELINE_SECURITY: float = 0.15
    CS_WEIGHT_BIAS_FAIRNESS: float = 0.10
    CS_WEIGHT_RETENTION: float = 0.10
    CS_WEIGHT_INCIDENT_REPORTING: float = 0.10
    CS_WEIGHT_HITL: float = 0.10

    # HITL Thresholds
    HITL_L0_CS_MIN: int = 90
    HITL_L0_CONF_MIN: float = 0.90
    HITL_L1_CS_MIN: int = 70
    HITL_L1_CONF_MIN: float = 0.75
    HITL_L2_CS_MIN: int = 50
    HITL_L2_CONF_MIN: float = 0.50
    HITL_L3_CS_MAX: int = 50
    HITL_L4_TRIGGER: str = "prompt_injection,compromise"

    # Encryption
    ENCRYPTION_KEY: str = "change-me-32-byte-encryption-key"
    TLS_ENABLED: bool = True

    # NIS2 Incident Reporting Deadlines (hours)
    NIS2_PRELIMINARY_DEADLINE_HOURS: int = 24
    NIS2_DETAILED_DEADLINE_HOURS: int = 72
    NIS2_FINAL_DEADLINE_DAYS: int = 30

    # Audit Trail
    AUDIT_RETENTION_YEARS: int = 7
    AUDIT_OPERATIONAL_LOGS_DAYS: int = 90
    AUDIT_LLM_DECISIONS_DAYS: int = 365

    # Observability
    PROMETHEUS_ENABLED: bool = True
    GRAFANA_URL: Optional[str] = None

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> list:
        return _parse_list(self.CORS_ORIGINS)

    @property
    def roles_list(self) -> list:
        return _parse_list(self.ROLES)

    @property
    def pii_languages_list(self) -> list:
        return _parse_list(self.PII_SUPPORTED_LANGUAGES)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
