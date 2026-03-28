from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from typing import Any

import asyncssh
import httpx

from app.core.crypto import SecretCipher
from app.core.database import Database
from app.core.database import utc_now_iso
from app.schemas.site import (
    CreateSiteRequest,
    DeploySiteResponse,
    SiteDeployment,
    SiteStatus,
    SiteSummary,
    UpdateSiteRequest,
)

logger = logging.getLogger(__name__)

_DEPLOY_REPO_URL = "https://github.com/iPythoning/wordpress-trade-starter.git"
_DEPLOY_BASE_DIR = "/opt/sites"


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:80] or "site"


class SitesService:
    def __init__(self, database: Database, cipher: SecretCipher) -> None:
        self._db = database
        self._cipher = cipher
        self._deploy_tasks: dict[str, asyncio.Task[None]] = {}

    # -- CRUD --

    def list_sites(self) -> list[SiteSummary]:
        rows = self._db.list_sites()
        return [SiteSummary.from_record(r) for r in rows]

    def create_site(self, payload: CreateSiteRequest) -> SiteSummary:
        site_id = uuid.uuid4().hex
        slug = payload.slug or _slugify(payload.display_name)

        # Ensure slug uniqueness
        existing = self._db.get_site_by_slug(slug) if hasattr(self._db, "get_site_by_slug") else None
        if existing:
            slug = f"{slug}-{site_id[:6]}"

        mysql_database = payload.mysql_database or slug.replace("-", "_")
        mysql_user = payload.mysql_user or slug.replace("-", "_")
        mysql_password = payload.mysql_password or uuid.uuid4().hex[:16]

        encrypted_ssh_password = self._cipher.encrypt(payload.ssh_password)
        encrypted_wp_admin_password = (
            self._cipher.encrypt(payload.wp_admin_password) if payload.wp_admin_password else None
        )
        encrypted_mysql_password = self._cipher.encrypt(mysql_password)
        encrypted_mysql_root_password = self._cipher.encrypt(payload.mysql_root_password)

        encrypted_cloudflare_api_token = (
            self._cipher.encrypt(payload.cloudflare_api_token) if payload.cloudflare_api_token else None
        )

        wp_plugins = payload.wp_plugins or []
        ssl_mode = payload.ssl_mode.value if payload.ssl_mode else "none"

        self._db.create_site(
            site_id=site_id,
            display_name=payload.display_name,
            slug=slug,
            domain=payload.domain,
            server_ip=payload.server_ip,
            ssh_user=payload.ssh_user,
            encrypted_ssh_password=encrypted_ssh_password,
            wp_admin_user=payload.wp_admin_user or "admin",
            encrypted_wp_admin_password=encrypted_wp_admin_password,
            wp_admin_email=payload.wp_admin_email,
            mysql_database=mysql_database,
            mysql_user=mysql_user,
            encrypted_mysql_password=encrypted_mysql_password,
            encrypted_mysql_root_password=encrypted_mysql_root_password,
            ssl_mode=ssl_mode,
            cloudflare_zone_id=payload.cloudflare_zone_id,
            encrypted_cloudflare_api_token=encrypted_cloudflare_api_token,
            cloudflare_dns_proxy=payload.cloudflare_dns_proxy or False,
            wp_plugins_json=json.dumps(wp_plugins),
            note=payload.note,
        )

        record = self._db.get_site(site_id)
        if record is None:
            raise RuntimeError("Failed to retrieve created site")
        return SiteSummary.from_record(record)

    def get_site(self, site_id: str) -> SiteSummary:
        record = self._db.get_site(site_id)
        if record is None:
            raise LookupError(f"Site {site_id} not found")
        return SiteSummary.from_record(record)

    def update_site(self, site_id: str, payload: UpdateSiteRequest) -> SiteSummary:
        record = self._db.get_site(site_id)
        if record is None:
            raise LookupError(f"Site {site_id} not found")

        fields: dict[str, Any] = {}
        for field_name, value in payload.model_dump(exclude_unset=True).items():
            if value is None:
                continue
            if field_name == "ssh_password":
                fields["encrypted_ssh_password"] = self._cipher.encrypt(value)
            elif field_name == "wp_admin_password":
                fields["encrypted_wp_admin_password"] = self._cipher.encrypt(value)
            elif field_name == "mysql_password":
                fields["encrypted_mysql_password"] = self._cipher.encrypt(value)
            elif field_name == "mysql_root_password":
                fields["encrypted_mysql_root_password"] = self._cipher.encrypt(value)
            elif field_name == "cloudflare_api_token":
                fields["encrypted_cloudflare_api_token"] = self._cipher.encrypt(value)
            elif field_name == "ssl_mode":
                fields["ssl_mode"] = value.value if hasattr(value, "value") else value
            elif field_name == "cloudflare_dns_proxy":
                fields["cloudflare_dns_proxy"] = int(value)
            elif field_name == "wp_plugins":
                fields["wp_plugins_json"] = json.dumps(value)
            else:
                fields[field_name] = value

        if fields:
            self._db.update_site(site_id, **fields)

        updated = self._db.get_site(site_id)
        if updated is None:
            raise RuntimeError("Failed to retrieve updated site")
        return SiteSummary.from_record(updated)

    def delete_site(self, site_id: str) -> None:
        record = self._db.get_site(site_id)
        if record is None:
            raise LookupError(f"Site {site_id} not found")
        if record["status"] == SiteStatus.DEPLOYING.value:
            raise RuntimeError("Cannot delete a site while it is deploying")
        self._db.delete_site(site_id)

    # -- Deploy --

    async def deploy_site(self, site_id: str) -> DeploySiteResponse:
        record = self._db.get_site(site_id)
        if record is None:
            raise LookupError(f"Site {site_id} not found")
        if record["status"] == SiteStatus.DEPLOYING.value:
            raise RuntimeError("Site is already deploying")

        deployment_id = uuid.uuid4().hex
        self._db.create_deployment(deployment_id=deployment_id, site_id=site_id)
        self._db.update_site(site_id, status=SiteStatus.DEPLOYING.value, deploy_log=None)

        task = asyncio.create_task(self._deploy(deployment_id, site_id))
        self._deploy_tasks[deployment_id] = task
        task.add_done_callback(lambda _: self._deploy_tasks.pop(deployment_id, None))

        site = SiteSummary.from_record(self._db.get_site(site_id))  # type: ignore[arg-type]
        deployment = SiteDeployment.from_record(self._db.get_deployment(deployment_id))  # type: ignore[arg-type]
        return DeploySiteResponse(site=site, deployment=deployment)

    def list_deployments(self, site_id: str) -> list[SiteDeployment]:
        rows = self._db.list_deployments_by_site(site_id)
        return [SiteDeployment.from_record(r) for r in rows]

    async def shutdown(self) -> None:
        for task in self._deploy_tasks.values():
            task.cancel()
        if self._deploy_tasks:
            await asyncio.gather(*self._deploy_tasks.values(), return_exceptions=True)
        self._deploy_tasks.clear()

    # -- Internal deploy logic --

    async def _deploy(self, deployment_id: str, site_id: str) -> None:
        log_lines: list[str] = []

        def _log(msg: str) -> None:
            log_lines.append(msg)
            logger.info("[deploy:%s] %s", deployment_id[:8], msg)

        try:
            self._db.update_deployment(deployment_id, status="running")
            record = self._db.get_site(site_id)
            if record is None:
                raise RuntimeError("Site record disappeared during deployment")

            slug = record["slug"]
            domain = record["domain"]
            server_ip = record["server_ip"]
            ssh_user = record["ssh_user"]
            ssh_password = self._cipher.decrypt(record["encrypted_ssh_password"])
            mysql_root_password = self._cipher.decrypt(record["encrypted_mysql_root_password"])
            mysql_password = self._cipher.decrypt(record["encrypted_mysql_password"])
            mysql_database = record["mysql_database"]
            mysql_user = record["mysql_user"]
            wp_plugins = json.loads(record.get("wp_plugins_json", "[]"))
            ssl_mode = record["ssl_mode"]

            deploy_dir = f"{_DEPLOY_BASE_DIR}/{slug}"

            _log(f"Connecting to {ssh_user}@{server_ip}...")
            async with asyncssh.connect(
                host=server_ip,
                username=ssh_user,
                password=ssh_password,
                known_hosts=None,
            ) as conn:
                # Step 1: Check Docker
                _log("Checking Docker availability...")
                result = await conn.run("docker --version", check=False)
                if result.exit_status != 0:
                    raise RuntimeError("Docker is not installed or not accessible")
                _log(f"Docker found: {result.stdout.strip()}")

                # Step 2: Clone repo
                _log(f"Preparing deploy directory: {deploy_dir}")
                await conn.run(f"mkdir -p {deploy_dir}", check=True)

                # Remove existing repo if present, then clone
                await conn.run(f"rm -rf {deploy_dir}/wordpress-trade-starter", check=False)
                _log("Cloning wordpress-trade-starter repository...")
                result = await conn.run(
                    f"git clone {_DEPLOY_REPO_URL} {deploy_dir}/wordpress-trade-starter",
                    check=False,
                )
                if result.exit_status != 0:
                    raise RuntimeError(f"git clone failed: {result.stderr.strip()}")
                _log("Repository cloned successfully")

                # Step 3: Write .env file
                env_content = (
                    f"MYSQL_ROOT_PASSWORD={mysql_root_password}\n"
                    f"MYSQL_DATABASE={mysql_database}\n"
                    f"MYSQL_USER={mysql_user}\n"
                    f"MYSQL_PASSWORD={mysql_password}\n"
                    f"WORDPRESS_DOMAIN={domain}\n"
                )
                _log("Writing .env configuration...")
                async with conn.start_sftp_client() as sftp:
                    async with sftp.open(f"{deploy_dir}/wordpress-trade-starter/.env", "w") as f:
                        await f.write(env_content)

                # Step 4: Docker compose up
                _log("Starting Docker containers...")
                result = await conn.run(
                    f"cd {deploy_dir}/wordpress-trade-starter && docker compose up -d",
                    check=False,
                )
                if result.exit_status != 0:
                    raise RuntimeError(f"docker compose up failed: {result.stderr.strip()}")
                _log("Docker containers started")

                # Step 5: Wait for health check
                _log("Waiting for services to be healthy...")
                await asyncio.sleep(15)

                # Step 6: Install WordPress plugins via WP-CLI (if available)
                if wp_plugins:
                    _log(f"Installing {len(wp_plugins)} WordPress plugins...")
                    for plugin_slug in wp_plugins:
                        result = await conn.run(
                            f"cd {deploy_dir}/wordpress-trade-starter && "
                            f"docker compose exec -T wordpress "
                            f"wp plugin install {plugin_slug} --activate --allow-root",
                            check=False,
                        )
                        if result.exit_status == 0:
                            _log(f"  Installed: {plugin_slug}")
                        else:
                            _log(f"  Skipped: {plugin_slug} ({result.stderr.strip()[:100]})")

            # Step 7: Cloudflare DNS (outside SSH session)
            if ssl_mode == "cloudflare" and record.get("encrypted_cloudflare_api_token") and record.get("cloudflare_zone_id"):
                _log("Configuring Cloudflare DNS...")
                cf_token = self._cipher.decrypt(record["encrypted_cloudflare_api_token"])
                cf_zone = record["cloudflare_zone_id"]
                cf_proxy = bool(record.get("cloudflare_dns_proxy"))
                await self._configure_cloudflare_dns(cf_token, cf_zone, domain, server_ip, cf_proxy, _log)

            site_url = f"https://{domain}"
            wp_admin_url = f"https://{domain}/wp-admin"
            _log(f"Deployment complete! Site: {site_url}")

            self._db.update_site(
                site_id,
                status=SiteStatus.RUNNING.value,
                site_url=site_url,
                wp_admin_url=wp_admin_url,
                deployed_at=utc_now_iso(),
                deploy_log="\n".join(log_lines),
            )
            self._db.update_deployment(
                deployment_id,
                status="completed",
                log="\n".join(log_lines),
                completed_at=utc_now_iso(),
            )

        except Exception as exc:
            error_msg = f"Deployment failed: {exc}"
            log_lines.append(error_msg)
            logger.error("[deploy:%s] %s", deployment_id[:8], error_msg)

            self._db.update_site(
                site_id,
                status=SiteStatus.ERROR.value,
                deploy_log="\n".join(log_lines),
            )
            self._db.update_deployment(
                deployment_id,
                status="failed",
                log="\n".join(log_lines),
                completed_at=utc_now_iso(),
            )

    async def _configure_cloudflare_dns(
        self,
        api_token: str,
        zone_id: str,
        domain: str,
        server_ip: str,
        proxied: bool,
        log: Any,
    ) -> None:
        base_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }
        record_payload = {
            "type": "A",
            "name": domain,
            "content": server_ip,
            "proxied": proxied,
            "ttl": 1 if proxied else 3600,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            # Check existing record
            resp = await client.get(
                base_url,
                params={"name": domain, "type": "A"},
                headers=headers,
            )
            existing = resp.json().get("result", [])

            if existing:
                record_id = existing[0]["id"]
                resp = await client.put(
                    f"{base_url}/{record_id}",
                    json=record_payload,
                    headers=headers,
                )
                if resp.status_code in (200, 201):
                    log("Cloudflare DNS A record updated")
                else:
                    log(f"Cloudflare DNS update warning: {resp.text[:100]}")
            else:
                resp = await client.post(
                    base_url,
                    json=record_payload,
                    headers=headers,
                )
                if resp.status_code in (200, 201):
                    log("Cloudflare DNS A record created")
                else:
                    log(f"Cloudflare DNS create warning: {resp.text[:100]}")
