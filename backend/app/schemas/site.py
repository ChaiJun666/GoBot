from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SiteStatus(str, Enum):
    DRAFT = "draft"
    DEPLOYING = "deploying"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class SslMode(str, Enum):
    NONE = "none"
    LETSENCRYPT = "letsencrypt"
    CLOUDFLARE = "cloudflare"


class DeploymentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Recommended WordPress plugin stack (from wordpress-trade-starter)
WP_PLUGIN_PRESETS: list[dict[str, str]] = [
    {"slug": "astra", "label": "Astra Theme"},
    {"slug": "elementor", "label": "Elementor"},
    {"slug": "seo-by-rank-math", "label": "Rank Math SEO"},
    {"slug": "wp-super-cache", "label": "WP Super Cache"},
    {"slug": "imagify", "label": "Imagify"},
    {"slug": "jetpack-boost", "label": "Jetpack Boost"},
    {"slug": "polylang", "label": "Polylang"},
    {"slug": "contact-form-7", "label": "Contact Form 7"},
    {"slug": "chaty", "label": "Chaty"},
    {"slug": "ecommerce-product-catalog", "label": "eCommerce Product Catalog"},
]


class CreateSiteRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    domain: str = Field(min_length=1, max_length=253)
    server_ip: str = Field(min_length=7, max_length=45)
    ssh_user: str = Field(min_length=1, max_length=120)
    ssh_password: str = Field(min_length=1, max_length=500)
    wp_admin_email: str = Field(min_length=1, max_length=253)
    mysql_root_password: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, min_length=1, max_length=120)
    wp_admin_user: str | None = Field(default=None, min_length=1, max_length=120)
    wp_admin_password: str | None = Field(default=None, min_length=1, max_length=120)
    mysql_database: str | None = Field(default=None, min_length=1, max_length=120)
    mysql_user: str | None = Field(default=None, min_length=1, max_length=120)
    mysql_password: str | None = Field(default=None, min_length=1, max_length=120)
    ssl_mode: SslMode | None = Field(default=None)
    cloudflare_zone_id: str | None = Field(default=None, max_length=120)
    cloudflare_api_token: str | None = Field(default=None, max_length=500)
    cloudflare_dns_proxy: bool | None = Field(default=None)
    wp_plugins: list[str] | None = Field(default=None)
    note: str | None = Field(default=None, max_length=500)


class UpdateSiteRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    domain: str | None = Field(default=None, min_length=1, max_length=253)
    server_ip: str | None = Field(default=None, min_length=7, max_length=45)
    ssh_user: str | None = Field(default=None, min_length=1, max_length=120)
    ssh_password: str | None = Field(default=None, min_length=1, max_length=500)
    wp_admin_user: str | None = Field(default=None, min_length=1, max_length=120)
    wp_admin_password: str | None = Field(default=None, min_length=1, max_length=120)
    wp_admin_email: str | None = Field(default=None, min_length=1, max_length=253)
    mysql_root_password: str | None = Field(default=None, min_length=1, max_length=120)
    mysql_database: str | None = Field(default=None, min_length=1, max_length=120)
    mysql_user: str | None = Field(default=None, min_length=1, max_length=120)
    mysql_password: str | None = Field(default=None, min_length=1, max_length=120)
    ssl_mode: SslMode | None = Field(default=None)
    cloudflare_zone_id: str | None = Field(default=None, max_length=120)
    cloudflare_api_token: str | None = Field(default=None, max_length=500)
    cloudflare_dns_proxy: bool | None = Field(default=None)
    wp_plugins: list[str] | None = Field(default=None)
    note: str | None = Field(default=None, max_length=500)


class SiteSummary(BaseModel):
    id: str
    display_name: str
    slug: str
    domain: str
    server_ip: str
    ssh_user: str
    has_ssh_password: bool = False
    wp_admin_user: str = "admin"
    has_wp_admin_password: bool = False
    wp_admin_email: str
    mysql_database: str
    mysql_user: str
    has_mysql_password: bool = False
    ssl_mode: str = "none"
    cloudflare_zone_id: str | None = None
    has_cloudflare_api_token: bool = False
    cloudflare_dns_proxy: bool = False
    wp_plugins: list[str] = Field(default_factory=list)
    status: str = "draft"
    deploy_log: str | None = None
    site_url: str | None = None
    wp_admin_url: str | None = None
    deployed_at: datetime | None = None
    note: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_record(cls, record: dict) -> "SiteSummary":
        return cls.model_validate(record)


class SiteDeployment(BaseModel):
    id: str
    site_id: str
    status: str = "pending"
    log: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    @classmethod
    def from_record(cls, record: dict) -> "SiteDeployment":
        return cls.model_validate(record)


class DeploySiteResponse(BaseModel):
    site: SiteSummary
    deployment: SiteDeployment
