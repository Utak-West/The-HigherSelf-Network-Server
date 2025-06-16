"""
Enterprise Database Configuration for The HigherSelf Network Server.

This module provides comprehensive database configuration supporting multiple
enterprise database systems while maintaining the HigherSelf Network values
of community, ecosystem, and spirit.
"""

import os
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote_plus

from pydantic import BaseSettings, Field, validator


class DatabaseType(str, Enum):
    """Supported enterprise database types."""
    
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MARIADB = "mariadb"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"
    SQLITE = "sqlite"  # For development/testing


class DatabaseEnvironment(str, Enum):
    """Database deployment environments."""
    
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class ConnectionPoolConfig(BaseSettings):
    """Database connection pool configuration."""
    
    # Connection pool settings
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")
    pool_pre_ping: bool = Field(default=True, env="DB_POOL_PRE_PING")
    
    # Connection settings
    connect_timeout: int = Field(default=10, env="DB_CONNECT_TIMEOUT")
    command_timeout: int = Field(default=30, env="DB_COMMAND_TIMEOUT")
    
    @validator("pool_size", "max_overflow")
    def validate_positive_integers(cls, v):
        if v < 1:
            raise ValueError("Pool size values must be positive integers")
        return v


class DatabaseSecurityConfig(BaseSettings):
    """Database security configuration."""
    
    # Encryption settings
    ssl_enabled: bool = Field(default=True, env="DB_SSL_ENABLED")
    ssl_cert_path: Optional[str] = Field(default=None, env="DB_SSL_CERT_PATH")
    ssl_key_path: Optional[str] = Field(default=None, env="DB_SSL_KEY_PATH")
    ssl_ca_path: Optional[str] = Field(default=None, env="DB_SSL_CA_PATH")
    
    # Authentication
    require_auth: bool = Field(default=True, env="DB_REQUIRE_AUTH")
    min_password_length: int = Field(default=12, env="DB_MIN_PASSWORD_LENGTH")
    
    # Audit settings
    audit_enabled: bool = Field(default=True, env="DB_AUDIT_ENABLED")
    audit_table_prefix: str = Field(default="audit_", env="DB_AUDIT_TABLE_PREFIX")
    
    # Access control
    read_only_users: List[str] = Field(default_factory=list, env="DB_READ_ONLY_USERS")
    admin_users: List[str] = Field(default_factory=list, env="DB_ADMIN_USERS")


class DatabaseBackupConfig(BaseSettings):
    """Database backup and recovery configuration."""
    
    # Backup settings
    backup_enabled: bool = Field(default=True, env="DB_BACKUP_ENABLED")
    backup_schedule: str = Field(default="0 2 * * *", env="DB_BACKUP_SCHEDULE")  # Daily at 2 AM
    backup_retention_days: int = Field(default=30, env="DB_BACKUP_RETENTION_DAYS")
    backup_location: str = Field(default="./backups", env="DB_BACKUP_LOCATION")
    
    # Point-in-time recovery
    pitr_enabled: bool = Field(default=True, env="DB_PITR_ENABLED")
    wal_archive_enabled: bool = Field(default=True, env="DB_WAL_ARCHIVE_ENABLED")
    
    # Cross-region replication
    replication_enabled: bool = Field(default=False, env="DB_REPLICATION_ENABLED")
    replica_hosts: List[str] = Field(default_factory=list, env="DB_REPLICA_HOSTS")


class DatabaseConfig(BaseSettings):
    """Main database configuration supporting multiple enterprise database systems."""
    
    # Database type and environment
    database_type: DatabaseType = Field(default=DatabaseType.POSTGRESQL, env="DATABASE_TYPE")
    environment: DatabaseEnvironment = Field(default=DatabaseEnvironment.DEVELOPMENT, env="DB_ENVIRONMENT")
    
    # Connection details
    host: str = Field(default="localhost", env="DATABASE_HOST")
    port: int = Field(default=5432, env="DATABASE_PORT")
    database: str = Field(default="higherself_network", env="DATABASE_NAME")
    username: str = Field(default="higherself_user", env="DATABASE_USER")
    password: str = Field(default="", env="DATABASE_PASSWORD")
    
    # Schema and table prefix
    schema: Optional[str] = Field(default=None, env="DATABASE_SCHEMA")
    table_prefix: str = Field(default="hs_", env="DATABASE_TABLE_PREFIX")
    
    # Component configurations
    pool_config: ConnectionPoolConfig = Field(default_factory=ConnectionPoolConfig)
    security_config: DatabaseSecurityConfig = Field(default_factory=DatabaseSecurityConfig)
    backup_config: DatabaseBackupConfig = Field(default_factory=DatabaseBackupConfig)
    
    # Feature flags
    enable_migrations: bool = Field(default=True, env="DB_ENABLE_MIGRATIONS")
    enable_query_logging: bool = Field(default=False, env="DB_ENABLE_QUERY_LOGGING")
    enable_performance_monitoring: bool = Field(default=True, env="DB_ENABLE_PERFORMANCE_MONITORING")
    
    @validator("port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @validator("password")
    def validate_password(cls, v, values):
        if values.get("environment") == DatabaseEnvironment.PRODUCTION and len(v) < 12:
            raise ValueError("Production database password must be at least 12 characters")
        return v
    
    def get_default_port(self) -> int:
        """Get default port for database type."""
        port_mapping = {
            DatabaseType.POSTGRESQL: 5432,
            DatabaseType.MYSQL: 3306,
            DatabaseType.MARIADB: 3306,
            DatabaseType.SQLSERVER: 1433,
            DatabaseType.ORACLE: 1521,
            DatabaseType.SQLITE: 0,  # Not applicable
        }
        return port_mapping.get(self.database_type, 5432)
    
    def get_connection_url(self) -> str:
        """Generate database connection URL."""
        if self.database_type == DatabaseType.SQLITE:
            return f"sqlite:///{self.database}.db"
        
        # URL encode password to handle special characters
        encoded_password = quote_plus(self.password) if self.password else ""
        auth_part = f"{self.username}:{encoded_password}@" if self.username else ""
        
        # Database-specific URL formats
        if self.database_type == DatabaseType.POSTGRESQL:
            driver = "postgresql+psycopg2"
        elif self.database_type == DatabaseType.MYSQL:
            driver = "mysql+pymysql"
        elif self.database_type == DatabaseType.MARIADB:
            driver = "mysql+pymysql"  # MariaDB uses MySQL driver
        elif self.database_type == DatabaseType.SQLSERVER:
            driver = "mssql+pyodbc"
        elif self.database_type == DatabaseType.ORACLE:
            driver = "oracle+cx_oracle"
        else:
            driver = "postgresql+psycopg2"  # Default fallback
        
        base_url = f"{driver}://{auth_part}{self.host}:{self.port}/{self.database}"
        
        # Add SSL parameters if enabled
        if self.security_config.ssl_enabled and self.database_type != DatabaseType.SQLITE:
            ssl_params = []
            if self.database_type == DatabaseType.POSTGRESQL:
                ssl_params.append("sslmode=require")
            elif self.database_type in [DatabaseType.MYSQL, DatabaseType.MARIADB]:
                ssl_params.append("ssl_disabled=false")
            
            if ssl_params:
                base_url += "?" + "&".join(ssl_params)
        
        return base_url
    
    def get_engine_kwargs(self) -> Dict[str, Any]:
        """Get SQLAlchemy engine configuration."""
        kwargs = {
            "pool_size": self.pool_config.pool_size,
            "max_overflow": self.pool_config.max_overflow,
            "pool_timeout": self.pool_config.pool_timeout,
            "pool_recycle": self.pool_config.pool_recycle,
            "pool_pre_ping": self.pool_config.pool_pre_ping,
            "echo": self.enable_query_logging,
        }
        
        # Database-specific configurations
        if self.database_type == DatabaseType.POSTGRESQL:
            kwargs.update({
                "connect_args": {
                    "connect_timeout": self.pool_config.connect_timeout,
                    "command_timeout": self.pool_config.command_timeout,
                }
            })
        elif self.database_type in [DatabaseType.MYSQL, DatabaseType.MARIADB]:
            kwargs.update({
                "connect_args": {
                    "connect_timeout": self.pool_config.connect_timeout,
                    "read_timeout": self.pool_config.command_timeout,
                    "write_timeout": self.pool_config.command_timeout,
                }
            })
        elif self.database_type == DatabaseType.SQLSERVER:
            kwargs.update({
                "connect_args": {
                    "timeout": self.pool_config.command_timeout,
                }
            })
        
        return kwargs
    
    def get_table_name(self, base_name: str) -> str:
        """Get full table name with prefix."""
        return f"{self.table_prefix}{base_name}"
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == DatabaseEnvironment.PRODUCTION
    
    def validate_connection_requirements(self) -> List[str]:
        """Validate database connection requirements."""
        errors = []
        
        if not self.host:
            errors.append("Database host is required")
        
        if not self.database:
            errors.append("Database name is required")
        
        if self.database_type != DatabaseType.SQLITE:
            if not self.username:
                errors.append("Database username is required")
            
            if self.is_production() and not self.password:
                errors.append("Database password is required in production")
        
        if self.security_config.ssl_enabled and self.is_production():
            if self.database_type == DatabaseType.POSTGRESQL and not self.security_config.ssl_cert_path:
                errors.append("SSL certificate path required for production PostgreSQL")
        
        return errors


class MultiDatabaseConfig(BaseSettings):
    """Configuration for multiple database connections."""
    
    # Primary database (required)
    primary: DatabaseConfig = Field(default_factory=DatabaseConfig)
    
    # Read replicas (optional)
    read_replicas: List[DatabaseConfig] = Field(default_factory=list)
    
    # Analytics database (optional)
    analytics: Optional[DatabaseConfig] = Field(default=None)
    
    # Cache database (Redis/etc.)
    cache: Optional[DatabaseConfig] = Field(default=None)
    
    # Load balancing settings
    enable_read_write_split: bool = Field(default=False, env="DB_ENABLE_READ_WRITE_SPLIT")
    read_replica_weight: Dict[str, float] = Field(default_factory=dict)
    
    def get_read_database(self) -> DatabaseConfig:
        """Get database configuration for read operations."""
        if self.enable_read_write_split and self.read_replicas:
            # Simple round-robin for now, could be enhanced with weighted selection
            return self.read_replicas[0]
        return self.primary
    
    def get_write_database(self) -> DatabaseConfig:
        """Get database configuration for write operations."""
        return self.primary


# Global database configuration instance
database_config = DatabaseConfig()
multi_db_config = MultiDatabaseConfig()

# Database-specific requirements mapping
DATABASE_REQUIREMENTS = {
    DatabaseType.POSTGRESQL: ["psycopg2-binary", "sqlalchemy"],
    DatabaseType.MYSQL: ["PyMySQL", "sqlalchemy"],
    DatabaseType.MARIADB: ["PyMySQL", "sqlalchemy"],
    DatabaseType.SQLSERVER: ["pyodbc", "sqlalchemy"],
    DatabaseType.ORACLE: ["cx_Oracle", "sqlalchemy"],
    DatabaseType.SQLITE: ["sqlalchemy"],
}

def get_database_requirements(db_type: DatabaseType) -> List[str]:
    """Get Python package requirements for database type."""
    return DATABASE_REQUIREMENTS.get(db_type, ["sqlalchemy"])

def validate_database_setup() -> Dict[str, Any]:
    """Validate current database setup and return status."""
    config = database_config
    
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "recommendations": []
    }
    
    # Validate connection requirements
    errors = config.validate_connection_requirements()
    if errors:
        validation_result["valid"] = False
        validation_result["errors"].extend(errors)
    
    # Production-specific validations
    if config.is_production():
        if not config.security_config.ssl_enabled:
            validation_result["warnings"].append("SSL should be enabled in production")
        
        if not config.backup_config.backup_enabled:
            validation_result["warnings"].append("Backups should be enabled in production")
        
        if config.pool_config.pool_size < 10:
            validation_result["recommendations"].append("Consider increasing pool size for production")
    
    # Performance recommendations
    if config.database_type == DatabaseType.POSTGRESQL:
        validation_result["recommendations"].append("Consider using connection pooling with PgBouncer for high-traffic applications")
    
    return validation_result
