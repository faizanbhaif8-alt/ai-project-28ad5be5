"""
Configuration Manager for BotManager V2.5
Centralized configuration handling with environment variable support
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BotType(Enum):
    """Enumeration of supported bot types"""
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"
    WHATSAPP = "whatsapp"
    CUSTOM = "custom"


class AIModel(Enum):
    """Enumeration of supported AI models"""
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    CLAUDE_3 = "claude-3"
    GEMINI_PRO = "gemini-pro"
    LOCAL_LLM = "local-llm"


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    host: str = "localhost"
    port: int = 5432
    database: str = "botmanager"
    username: str = "postgres"
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False
    
    @property
    def connection_string(self) -> str:
        """Generate SQLAlchemy connection string"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class RedisConfig:
    """Redis configuration for caching and message queues"""
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0
    decode_responses: bool = True
    max_connections: int = 20
    
    @property
    def connection_url(self) -> str:
        """Generate Redis connection URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


@dataclass
class BotConfig:
    """Individual bot configuration"""
    name: str
    bot_type: BotType
    enabled: bool = True
    token: str = ""
    webhook_url: Optional[str] = None
    admin_ids: List[int] = None
    rate_limit: int = 30  # messages per minute
    ai_model: AIModel = AIModel.GPT_3_5_TURBO
    system_prompt: str = "You are a helpful assistant."
    max_tokens: int = 1000
    temperature: float = 0.7
    
    def __post_init__(self):
        """Initialize default values"""
        if self.admin_ids is None:
            self.admin_ids = []
        if isinstance(self.bot_type, str):
            self.bot_type = BotType(self.bot_type)
        if isinstance(self.ai_model, str):
            self.ai_model = AIModel(self.ai_model)


@dataclass
class APIConfig:
    """API server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    secret_key: str = ""
    cors_origins: List[str] = None
    rate_limit_per_minute: int = 60
    
    def __post_init__(self):
        """Initialize default values"""
        if self.cors_origins is None:
            self.cors_origins = ["*"]
        if not self.secret_key:
            self.secret_key = os.urandom(24).hex()


@dataclass
class MonitoringConfig:
    """Monitoring and logging configuration"""
    log_level: str = "INFO"
    enable_metrics: bool = True
    metrics_port: int = 9090
    enable_health_checks: bool = True
    sentry_dsn: Optional[str] = None
    log_file: Optional[str] = None


class Config:
    """
    Main configuration class that loads settings from environment variables
    and provides defaults for all configuration options.
    """
    
    def __init__(self):
        """Initialize configuration with environment variables"""
        self._load_from_env()
        self._validate_config()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # API Keys from Replit Secrets
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        self.telegram_api_key = os.getenv("TELEGRAM_API_KEY", "")
        self.discord_bot_token = os.getenv("DISCORD_BOT_TOKEN", "")
        self.slack_bot_token = os.getenv("SLACK_BOT_TOKEN", "")
        self.slack_app_token = os.getenv("SLACK_APP_TOKEN", "")
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        
        # Database configuration
        self.database = DatabaseConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "botmanager"),
            username=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )
        
        # Redis configuration
        self.redis = RedisConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD", ""),
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=os.getenv("REDIS_DECODE_RESPONSES", "true").lower() == "true",
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))
        )
        
        # API Server configuration
        self.api = APIConfig(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000")),
            debug=os.getenv("API_DEBUG", "false").lower() == "true",
            secret_key=os.getenv("API_SECRET_KEY", ""),
            cors_origins=os.getenv("CORS_ORIGINS", "*").split(","),
            rate_limit_per_minute=int(os.getenv("API_RATE_LIMIT", "60"))
        )
        
        # Monitoring configuration
        self.monitoring = MonitoringConfig(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
            metrics_port=int(os.getenv("METRICS_PORT", "9090")),
            enable_health_checks=os.getenv("ENABLE_HEALTH_CHECKS", "true").lower() == "true",
            sentry_dsn=os.getenv("SENTRY_DSN"),
            log_file=os.getenv("LOG_FILE")
        )
        
        # Bot configurations
        self.bots = self._load_bot_configs()
        
        # General settings
        self.project_name = os.getenv("PROJECT_NAME", "BotManager V2.5")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
        self.enable_webhooks = os.getenv("ENABLE_WEBHOOKS", "true").lower() == "true"
        self.webhook_secret = os.getenv("WEBHOOK_SECRET", "")
        self.max_concurrent_bots = int(os.getenv("MAX_CONCURRENT_BOTS", "10"))
        
        # AI Model defaults
        self.default_ai_model = AIModel(os.getenv("DEFAULT_AI_MODEL", "gpt-3.5-turbo"))
        self.default_max_tokens = int(os.getenv("DEFAULT_MAX_TOKENS", "1000"))
        self.default_temperature = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
    
    def _load_bot_configs(self) -> Dict[str, BotConfig]:
        """Load bot configurations from environment variables"""
        bots = {}
        
        # Parse bot configurations from environment
        # Format: BOT_<NAME>_TYPE, BOT_<NAME>_TOKEN, etc.
        env_vars = dict(os.environ)
        bot_names = set()
        
        for key in env_vars.keys():
            if key.startswith("BOT_") and "_TYPE" in key:
                bot_name = key.split("_")[1].lower()
                bot_names.add(bot_name)
        
        for bot_name in bot_names:
            try:
                bot_config = BotConfig(
                    name=bot_name,
                    bot_type=BotType(env_vars.get(f"BOT_{bot_name.upper()}_TYPE", "custom")),
                    enabled=env_vars.get(f"BOT_{bot_name.upper()}_ENABLED", "true").lower() == "true",
                    token=env_vars.get(f"BOT_{bot_name.upper()}_TOKEN", ""),
                    webhook_url=env_vars.get(f"BOT_{bot_name.upper()}_WEBHOOK_URL"),
                    admin_ids=[int(id.strip()) for id in env_vars.get(f"BOT_{bot_name.upper()}_ADMIN_IDS", "").split(",") if id.strip()],
                    rate_limit=int(env_vars.get(f"BOT_{bot_name.upper()}_RATE_LIMIT", "30")),
                    ai_model=AIModel(env_vars.get(f"BOT_{bot_name.upper()}_AI_MODEL", "gpt-3.5-turbo")),
                    system_prompt=env_vars.get(f"BOT_{bot_name.upper()}_SYSTEM_PROMPT", "You are a helpful assistant."),
                    max_tokens=int(env_vars.get(f"BOT_{bot_name.upper()}_MAX_TOKENS", "1000")),
                    temperature=float(env_vars.get(f"BOT_{bot_name.upper()}_TEMPERATURE", "0.7"))
                )
                bots[bot_name] = bot_config
                logger.info(f"Loaded configuration for bot: {bot_name}")
            except Exception as e:
                logger.error(f"Failed to load configuration for bot {bot_name}: {e}")
        
        # If no bots configured via environment, create a default Telegram bot
        if not bots:
            logger.warning("No bot configurations found in environment. Creating default bot.")
            default_bot = BotConfig(
                name="default",
                bot_type=BotType.TELEGRAM,
                enabled=False,  # Disabled by default since no token provided
                token=self.telegram_api_key,
                system_prompt="You are a helpful AI assistant integrated with Telegram."
            )
            bots["default"] = default_bot
        
        return bots
    
    def _validate_config(self):
        """Validate critical configuration values"""
        errors = []
        
        # Check for required API keys based on enabled bots
        for bot_name, bot_config in self.bots.items():
            if bot_config.enabled:
                if bot_config.bot_type == BotType.TELEGRAM and not bot_config.token:
                    errors.append(f"Telegram bot '{bot_name}' is enabled but no token provided")
                elif bot_config.bot_type == BotType.DISCORD and not bot_config.token:
                    errors.append(f"Discord bot '{bot_name}' is enabled but no token provided")
                
                # Check AI API keys based on selected model
                if bot_config.ai_model in [AIModel.GPT_4, AIModel.GPT_4_TURBO, AIModel.GPT_3_5_TURBO] and not self.openai_api_key:
                    errors.append(f"Bot '{bot_name}' uses OpenAI model but OPENAI_API_KEY is not set")
                elif bot_config.ai_model == AIModel.CLAUDE_3 and not self.anthropic_api_key:
                    errors.append(f"Bot '{bot_name}' uses Claude model but ANTHROPIC_API_KEY is not set")
                elif bot_config.ai_model == AIModel.GEMINI_PRO and not self.google_api_key:
                    errors.append(f"Bot '{bot_name}' uses Gemini model but GOOGLE_API_KEY is not set")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            logger.error(error_msg)
            if self.environment == "production":
                raise ValueError(error_msg)
    
    def get_bot_config(self, bot_name: str) -> Optional[BotConfig]:
        """Get configuration for a specific bot"""
        return self.bots.get(bot_name)
    
    def get_enabled_bots(self) -> Dict[str, BotConfig]:
        """Get all enabled bot configurations"""
        return {name: config for name, config in self.bots.items() if config.enabled}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        config_dict = {
            "project_name": self.project_name,
            "environment": self.environment,
            "base_url": self.base_url,
            "enable_webhooks": self.enable_webhooks,
            "max_concurrent_bots": self.max_concurrent_bots,
            "default_ai_model": self.default_ai_model.value,
            "default_max_tokens": self.default_max_tokens,
            "default_temperature": self.default_temperature,
            "database": asdict(self.database),
            "redis": asdict(self.redis),
            "api": asdict(self.api),
            "monitoring": asdict(self.monitoring),
            "bots": {name: asdict(config) for name, config in self.bots.items()}
        }
        
        # Add API keys (masked for security)
        config_dict["api_keys"] = {
            "openai_api_key": "***" if self.openai_api_key else "",
            "anthropic_api_key": "***" if self.anthropic_api_key else "",
            "google_api_key": "***" if self.google_api_key else "",
            "telegram_api_key": "***" if self.telegram_api_key else "",
            "discord_bot_token": "***" if self.discord_bot_token else "",
            "slack_bot_token": "***" if self.slack_bot_token else "",
            "slack_app_token": "***" if self.slack_app_token else "",
            "twilio_account_sid": "***" if self.twilio_account_sid else "",
            "twilio_auth_token": "***" if self.twilio_auth_token else ""
        }
        
        return config_dict
    
    def save_to_file(self, filepath: str = "config.json"):
        """Save configuration to JSON file (for debugging)"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        logger.info(f"Configuration saved to {filepath}")
    
    def __str__(self) -> str:
        """String representation of configuration"""
        config_summary = [
            f"Project: {self.project_name}",
            f"Environment: {self.environment}",
            f"Enabled Bots: {len(self.get_enabled_bots())}/{len(self.bots)}",
            f"Database: {self.database.host}:{self.database.port}",
            f"API Server: {self.api.host}:{self.api.port}",
            f"Redis: {self.redis.host}:{self.redis.port}"
        ]
        return "\n".join(config_summary)


# Global configuration instance
config = Config()

# Export for easy access
__all__ = ['config', 'Config', 'BotConfig', 'DatabaseConfig', 'RedisConfig', 
           'APIConfig', 'MonitoringConfig', 'BotType', 'AIModel']

if __name__ == "__main__":
    # Test the configuration
    print("=" * 50)
    print("BotManager V2.5 Configuration")
    print("=" * 50)
    print(config)
    print("\nEnabled Bots:")
    for name, bot_config in config.get_enabled_bots().items():
        print(f"  - {name} ({bot_config.bot_type.value})")
    
    # Save configuration to file for inspection
    config.save_to_file("config_dump.json")
    print(f"\nConfiguration saved to config_dump.json")