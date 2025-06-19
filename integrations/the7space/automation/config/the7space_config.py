"""
The 7 Space Main Configuration

Central configuration for The 7 Space Art Gallery & Wellness Center automation.
Integrates with existing HigherSelf Network Server infrastructure.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path

@dataclass
class The7SpaceConfig:
    """Main configuration for The 7 Space automation system"""
    
    # Business Entity Information
    entity_name: str = "The 7 Space"
    entity_id: str = "the_7_space"
    business_type: str = "art_gallery_wellness_center"
    
    # Contact Management
    total_contacts: int = 191
    primary_database: str = "the7space_contacts"
    
    # Notion Integration
    notion_api_token: str = field(default_factory=lambda: os.getenv("NOTION_API_TOKEN", ""))
    notion_database_ids: Dict[str, str] = field(default_factory=lambda: {
        "contacts": os.getenv("THE7SPACE_CONTACTS_DB", ""),
        "artworks": os.getenv("THE7SPACE_ARTWORKS_DB", ""),
        "artists": os.getenv("THE7SPACE_ARTISTS_DB", ""),
        "events": os.getenv("THE7SPACE_EVENTS_DB", ""),
        "services": os.getenv("THE7SPACE_SERVICES_DB", ""),
        "appointments": os.getenv("THE7SPACE_APPOINTMENTS_DB", ""),
        "classes": os.getenv("THE7SPACE_CLASSES_DB", ""),
        "sales": os.getenv("THE7SPACE_SALES_DB", ""),
        "marketing_campaigns": os.getenv("THE7SPACE_MARKETING_DB", ""),
        "analytics": os.getenv("THE7SPACE_ANALYTICS_DB", "")
    })
    
    # API Configuration
    api_base_url: str = field(default_factory=lambda: os.getenv("THE7SPACE_API_URL", "http://localhost:8000"))
    api_key: str = field(default_factory=lambda: os.getenv("THE7SPACE_API_KEY", ""))
    webhook_secret: str = field(default_factory=lambda: os.getenv("THE7SPACE_WEBHOOK_SECRET", ""))
    
    # Business Information
    business_info: Dict[str, str] = field(default_factory=lambda: {
        "name": "The 7 Space | Art Gallery & Wellness Center",
        "address": os.getenv("THE7SPACE_ADDRESS", ""),
        "phone": os.getenv("THE7SPACE_PHONE", ""),
        "email": os.getenv("THE7SPACE_EMAIL", "info@the7space.com"),
        "website": os.getenv("THE7SPACE_WEBSITE", "https://the7space.com"),
        "timezone": os.getenv("THE7SPACE_TIMEZONE", "America/Los_Angeles")
    })
    
    # Business Hours
    business_hours: Dict[str, Dict[str, str]] = field(default_factory=lambda: {
        "monday": {"open": "10:00", "close": "18:00"},
        "tuesday": {"open": "10:00", "close": "18:00"},
        "wednesday": {"open": "10:00", "close": "18:00"},
        "thursday": {"open": "10:00", "close": "18:00"},
        "friday": {"open": "10:00", "close": "18:00"},
        "saturday": {"open": "10:00", "close": "17:00"},
        "sunday": {"closed": True}
    })
    
    # Social Media Integration
    social_media: Dict[str, str] = field(default_factory=lambda: {
        "instagram": os.getenv("THE7SPACE_INSTAGRAM", ""),
        "facebook": os.getenv("THE7SPACE_FACEBOOK", ""),
        "twitter": os.getenv("THE7SPACE_TWITTER", ""),
        "linkedin": os.getenv("THE7SPACE_LINKEDIN", "")
    })
    
    # Email Configuration
    email_config: Dict[str, str] = field(default_factory=lambda: {
        "smtp_server": os.getenv("SMTP_SERVER", ""),
        "smtp_port": os.getenv("SMTP_PORT", "587"),
        "smtp_username": os.getenv("SMTP_USERNAME", ""),
        "smtp_password": os.getenv("SMTP_PASSWORD", ""),
        "from_email": os.getenv("THE7SPACE_FROM_EMAIL", "info@the7space.com"),
        "from_name": os.getenv("THE7SPACE_FROM_NAME", "The 7 Space")
    })
    
    # Payment Processing
    payment_config: Dict[str, str] = field(default_factory=lambda: {
        "stripe_public_key": os.getenv("STRIPE_PUBLIC_KEY", ""),
        "stripe_secret_key": os.getenv("STRIPE_SECRET_KEY", ""),
        "stripe_webhook_secret": os.getenv("STRIPE_WEBHOOK_SECRET", ""),
        "paypal_client_id": os.getenv("PAYPAL_CLIENT_ID", ""),
        "paypal_client_secret": os.getenv("PAYPAL_CLIENT_SECRET", "")
    })
    
    # File Storage
    storage_config: Dict[str, str] = field(default_factory=lambda: {
        "aws_access_key": os.getenv("AWS_ACCESS_KEY_ID", ""),
        "aws_secret_key": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        "aws_bucket": os.getenv("THE7SPACE_S3_BUCKET", ""),
        "aws_region": os.getenv("AWS_REGION", "us-west-2"),
        "local_storage_path": os.getenv("THE7SPACE_STORAGE_PATH", "./data/the7space")
    })
    
    # Logging Configuration
    logging_config: Dict[str, str] = field(default_factory=lambda: {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file_path": os.getenv("THE7SPACE_LOG_PATH", "./logs/the7space.log"),
        "max_file_size": os.getenv("LOG_MAX_SIZE", "10MB"),
        "backup_count": os.getenv("LOG_BACKUP_COUNT", "5")
    })
    
    # Redis Configuration
    redis_config: Dict[str, str] = field(default_factory=lambda: {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": os.getenv("REDIS_PORT", "6379"),
        "password": os.getenv("REDIS_PASSWORD", ""),
        "db": os.getenv("THE7SPACE_REDIS_DB", "2"),
        "prefix": "the7space:"
    })
    
    # MongoDB Configuration
    mongodb_config: Dict[str, str] = field(default_factory=lambda: {
        "uri": os.getenv("MONGODB_URI", "mongodb://localhost:27017/the7space"),
        "database": os.getenv("THE7SPACE_MONGODB_DB", "the7space"),
        "collection_prefix": "the7space_"
    })
    
    # Feature Flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        "gallery_automation": os.getenv("THE7SPACE_GALLERY_AUTOMATION", "true").lower() == "true",
        "wellness_automation": os.getenv("THE7SPACE_WELLNESS_AUTOMATION", "true").lower() == "true",
        "marketing_automation": os.getenv("THE7SPACE_MARKETING_AUTOMATION", "true").lower() == "true",
        "email_automation": os.getenv("THE7SPACE_EMAIL_AUTOMATION", "true").lower() == "true",
        "social_media_automation": os.getenv("THE7SPACE_SOCIAL_AUTOMATION", "true").lower() == "true",
        "analytics_tracking": os.getenv("THE7SPACE_ANALYTICS", "true").lower() == "true",
        "backup_automation": os.getenv("THE7SPACE_BACKUP_AUTOMATION", "true").lower() == "true"
    })
    
    # Environment Settings
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug_mode: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    testing_mode: bool = field(default_factory=lambda: os.getenv("TESTING_MODE", "false").lower() == "true")
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        self._validate_config()
        self._setup_directories()
    
    def _validate_config(self):
        """Validate required configuration values"""
        required_fields = [
            ("notion_api_token", "NOTION_API_TOKEN"),
            ("api_key", "THE7SPACE_API_KEY")
        ]
        
        missing_fields = []
        for field_name, env_var in required_fields:
            if not getattr(self, field_name):
                missing_fields.append(env_var)
        
        if missing_fields and not self.testing_mode:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}")
    
    def _setup_directories(self):
        """Create necessary directories"""
        directories = [
            self.storage_config["local_storage_path"],
            os.path.dirname(self.logging_config["file_path"]),
            "./data/the7space/gallery",
            "./data/the7space/wellness",
            "./data/the7space/marketing",
            "./data/the7space/backups"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def get_database_id(self, database_name: str) -> str:
        """Get Notion database ID by name"""
        return self.notion_database_ids.get(database_name, "")
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled"""
        return self.features.get(feature_name, False)
    
    def get_business_hours_for_day(self, day: str) -> Dict[str, str]:
        """Get business hours for a specific day"""
        return self.business_hours.get(day.lower(), {"closed": True})
    
    def is_business_open(self, day: str, time: str) -> bool:
        """Check if business is open at a specific day and time"""
        hours = self.get_business_hours_for_day(day)
        if hours.get("closed"):
            return False
        
        from datetime import datetime
        try:
            current_time = datetime.strptime(time, "%H:%M").time()
            open_time = datetime.strptime(hours["open"], "%H:%M").time()
            close_time = datetime.strptime(hours["close"], "%H:%M").time()
            return open_time <= current_time <= close_time
        except (ValueError, KeyError):
            return False

# Global configuration instance
the7space_config = The7SpaceConfig()
