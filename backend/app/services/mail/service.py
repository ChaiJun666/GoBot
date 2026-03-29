from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
import imaplib
import re
import sqlite3
import smtplib
from uuid import uuid4

from app.core.database import Database
from app.schemas.mail import (
    CreateMailboxRequest,
    LeadRecipientSummary,
    MailFolder,
    MailProviderConfig,
    MailboxSummary,
    MailboxSyncResponse,
    MailboxStatus,
    MailMessageDetail,
    MailMessageSummary,
    SendMailRequest,
    SendMailResponse,
    UpdateMailboxRequest,
)
from app.services.mail.crypto import MailSecretCipher
from app.services.mail.providers import MAIL_PROVIDER_CONFIGS, list_provider_configs

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SENT_FOLDER_HINTS = (
    "sent", "sent items", "sent messages", "Sent", "Sent Items",
    "已发送", "已发送邮件", "已发送邮件箱",
)


@dataclass
class ParsedMailMessage:
    remote_uid: str
    message_id: str | None
    subject: str
    from_name: str | None
    from_address: str | None
    to_summary: str | None
    snippet: str | None
    body_text: str | None
    is_read: bool
    sent_at: str | None
    received_at: str | None


class MailService:
    def __init__(self, *, database: Database, cipher: MailSecretCipher) -> None:
        self.database = database
        self.cipher = cipher

    def list_providers(self) -> list[MailProviderConfig]:
        return list_provider_configs()

    def list_mailboxes(self) -> list[MailboxSummary]:
        return [MailboxSummary.from_record(item) for item in self.database.list_mailboxes()]

    def create_mailbox(self, payload: CreateMailboxRequest) -> MailboxSummary:
        provider = MAIL_PROVIDER_CONFIGS[payload.provider]
        email_address = payload.email_address.strip()
        if not EMAIL_PATTERN.match(email_address):
            raise RuntimeError("Invalid mailbox email address")
        encrypted_secret = self.cipher.encrypt(payload.auth_secret)
        mailbox_id = str(uuid4())
        try:
            self.database.create_mailbox(
                mailbox_id=mailbox_id,
                provider=provider.key.value,
                email_address=email_address,
                note=(payload.note or "").strip() or None,
                imap_host=provider.imap_host,
                imap_port=provider.imap_port,
                smtp_host=provider.smtp_host,
                smtp_port=provider.smtp_port,
                smtp_starttls=provider.smtp_starttls,
                encrypted_auth_secret=encrypted_secret,
            )
        except sqlite3.IntegrityError as exc:
            raise RuntimeError("Mailbox already exists") from exc
        self.sync_mailbox(mailbox_id)
        mailbox = self.database.get_mailbox(mailbox_id)
        if mailbox is None:
            raise RuntimeError("Failed to create mailbox")
        return MailboxSummary.from_record(mailbox)

    def update_mailbox(self, mailbox_id: str, payload: UpdateMailboxRequest) -> MailboxSummary:
        mailbox = self.database.get_mailbox(mailbox_id)
        if mailbox is None:
            raise LookupError("Mailbox not found")

        encrypted_secret = None
        should_resync = False
        if payload.auth_secret:
            encrypted_secret = self.cipher.encrypt(payload.auth_secret)
            should_resync = True

        self.database.update_mailbox(
            mailbox_id,
            note=(payload.note or "").strip() or None,
            encrypted_auth_secret=encrypted_secret,
        )

        if should_resync:
            self.sync_mailbox(mailbox_id)

        refreshed = self.database.get_mailbox(mailbox_id)
        if refreshed is None:
            raise RuntimeError("Mailbox not found after update")
        return MailboxSummary.from_record(refreshed)

    def sync_mailbox(self, mailbox_id: str, *, limit: int = 50) -> MailboxSyncResponse:
        mailbox = self.database.get_mailbox(mailbox_id)
        if mailbox is None:
            raise LookupError("Mailbox not found")

        secret = self.cipher.decrypt(mailbox["encrypted_auth_secret"])
        imap = self._create_imap_client(mailbox["imap_host"], mailbox["imap_port"])
        inbox_count = 0
        sent_count = 0
        try:
            imap.login(mailbox["email_address"], secret)
            self._send_imap_id(imap)
            inbox_count = self._sync_folder(imap, mailbox_id, MailFolder.INBOX, "INBOX", limit)
            sent_folder = self._resolve_sent_folder(imap)
            if sent_folder is not None:
                sent_count = self._sync_folder(imap, mailbox_id, MailFolder.SENT, sent_folder, limit)
            self.database.mark_mailbox_ready(mailbox_id)
        except Exception as exc:
            self.database.mark_mailbox_error(mailbox_id, str(exc))
            raise RuntimeError(str(exc)) from exc
        finally:
            try:
                imap.logout()
            except Exception:
                pass

        refreshed = self.database.get_mailbox(mailbox_id)
        if refreshed is None:
            raise RuntimeError("Mailbox not found after sync")
        return MailboxSyncResponse(
            mailbox=MailboxSummary.from_record(refreshed),
            inbox_count=inbox_count,
            sent_count=sent_count,
        )

    def list_messages(self, mailbox_id: str, *, folder: MailFolder, limit: int = 20, offset: int = 0) -> list[MailMessageSummary]:
        mailbox = self.database.get_mailbox(mailbox_id)
        if mailbox is None:
            raise LookupError("Mailbox not found")
        return [
            MailMessageSummary.from_record(item)
            for item in self.database.list_mail_messages(mailbox_id=mailbox_id, folder=folder.value, limit=limit, offset=offset)
        ]

    def count_messages(self, mailbox_id: str, folder: MailFolder) -> int:
        mailbox = self.database.get_mailbox(mailbox_id)
        if mailbox is None:
            raise LookupError("Mailbox not found")
        return self.database.count_mail_messages(mailbox_id=mailbox_id, folder=folder.value)

    def get_message(self, message_id: str) -> MailMessageDetail:
        message = self.database.get_mail_message(message_id)
        if message is None:
            raise LookupError("Mail message not found")
        return MailMessageDetail.from_record(message)

    def send_mail(self, payload: SendMailRequest) -> SendMailResponse:
        mailbox = self.database.get_mailbox(payload.mailbox_id)
        if mailbox is None:
            raise LookupError("Mailbox not found")

        recipients = [item.strip() for item in payload.to if item.strip()]
        if not recipients:
            raise RuntimeError("At least one recipient is required")
        invalid = [item for item in recipients if not EMAIL_PATTERN.match(item)]
        if invalid:
            raise RuntimeError(f"Invalid recipient email: {invalid[0]}")

        secret = self.cipher.decrypt(mailbox["encrypted_auth_secret"])
        message = EmailMessage()
        message["From"] = mailbox["email_address"]
        message["To"] = ", ".join(recipients)
        message["Subject"] = payload.subject.strip()
        message.set_content(payload.body)

        smtp = self._create_smtp_client(
            host=mailbox["smtp_host"],
            port=mailbox["smtp_port"],
            use_starttls=bool(mailbox["smtp_starttls"]),
        )
        try:
            smtp.login(mailbox["email_address"], secret)
            smtp.send_message(message)
            self.database.mark_mailbox_ready(mailbox["id"])
            now = datetime.now(UTC).isoformat()
            snippet = (payload.body or "")[:200]
            self.database.upsert_mail_message(
                message_id=uuid4().hex,
                mailbox_id=mailbox["id"],
                folder="sent",
                remote_uid=uuid4().hex,
                message_id_header=message.get("Message-ID"),
                subject=payload.subject.strip(),
                from_name=None,
                from_address=mailbox["email_address"],
                to_summary=", ".join(recipients),
                snippet=snippet,
                body_text=payload.body,
                is_read=True,
                sent_at=now,
                received_at=None,
            )
        except Exception as exc:
            self.database.mark_mailbox_error(mailbox["id"], str(exc))
            raise RuntimeError(str(exc)) from exc
        finally:
            try:
                smtp.quit()
            except Exception:
                pass

        refreshed = self.database.get_mailbox(mailbox["id"])
        if refreshed is None:
            raise RuntimeError("Mailbox not found after send")
        return SendMailResponse(
            mailbox=MailboxSummary.from_record(refreshed),
            accepted=recipients,
            message="Mail sent successfully",
        )

    def list_lead_recipients(self, *, limit: int = 200) -> list[LeadRecipientSummary]:
        return [
            LeadRecipientSummary.model_validate(item)
            for item in self.database.list_lead_recipients(limit=limit)
        ]

    def _create_imap_client(self, host: str, port: int) -> imaplib.IMAP4_SSL:
        return imaplib.IMAP4_SSL(host=host, port=port)

    @staticmethod
    def _send_imap_id(imap: imaplib.IMAP4_SSL) -> None:
        """Send IMAP ID command (RFC 2971). Required by 163.com and other Chinese providers."""
        tag = imap._new_tag()
        imap.send(tag + b' ID ("name" "GoBot" "version" "1.0.0")\r\n')
        while True:
            line = imap.readline()
            if line.startswith(tag):
                break

    def _create_smtp_client(self, *, host: str, port: int, use_starttls: bool) -> smtplib.SMTP:
        if use_starttls:
            client = smtplib.SMTP(host=host, port=port, timeout=30)
            client.ehlo()
            client.starttls()
            client.ehlo()
            return client
        return smtplib.SMTP_SSL(host=host, port=port, timeout=30)

    def _resolve_sent_folder(self, imap: imaplib.IMAP4_SSL) -> str | None:
        status, folders = imap.list()
        if status != "OK" or folders is None:
            return None

        decoded: list[tuple[str, str]] = []  # (folder_name, flags_text)
        for raw in folders:
            text = raw.decode("utf-8", errors="ignore")
            # Extract flags from the first part (e.g. "(\\Sent)")
            flags_match = re.search(r"\(([^)]*)\)", text)
            flags_text = flags_match.group(1) if flags_match else ""
            # Extract folder name from the last quoted segment
            match = re.search(r'"([^"]+)"\s*$', text)
            if match:
                decoded.append((match.group(1), flags_text))
                continue
            parts = text.split(" ")
            decoded.append((parts[-1].strip('"'), flags_text))

        # Prefer IMAP \Sent flag
        for name, flags in decoded:
            if r"\Sent" in flags:
                return name

        # Fallback: match by name hints
        normalized_map = {name.casefold(): name for name, _ in decoded}
        for hint in SENT_FOLDER_HINTS:
            if hint in normalized_map:
                return normalized_map[hint]
            for normalized, original in normalized_map.items():
                if hint in normalized:
                    return original
        return None

    def _sync_folder(
        self,
        imap: imaplib.IMAP4_SSL,
        mailbox_id: str,
        folder: MailFolder,
        remote_folder: str,
        limit: int,
    ) -> int:
        status, _ = imap.select(f'"{remote_folder}"', readonly=False)
        if status != "OK":
            return 0

        status, data = imap.uid("search", None, "ALL")
        if status != "OK" or not data or not data[0]:
            return 0

        uids = data[0].decode("utf-8").split()
        selected = list(reversed(uids[-limit:]))
        for uid in selected:
            status, fetched = imap.uid("fetch", uid, "(RFC822 FLAGS)")
            if status != "OK" or not fetched:
                continue
            raw_message = next((part[1] for part in fetched if isinstance(part, tuple) and len(part) > 1), None)
            if not raw_message:
                continue
            flags_line = fetched[0][0].decode("utf-8", errors="ignore") if isinstance(fetched[0], tuple) else ""
            parsed = self._parse_message(uid=uid, raw_message=raw_message, flags_line=flags_line)
            message_id = f"{mailbox_id}:{folder.value}:{uid}"
            self.database.upsert_mail_message(
                message_id=message_id,
                mailbox_id=mailbox_id,
                folder=folder.value,
                remote_uid=uid,
                message_id_header=parsed.message_id,
                subject=parsed.subject,
                from_name=parsed.from_name,
                from_address=parsed.from_address,
                to_summary=parsed.to_summary,
                snippet=parsed.snippet,
                body_text=parsed.body_text,
                is_read=parsed.is_read,
                sent_at=parsed.sent_at,
                received_at=parsed.received_at,
            )
        return len(selected)

    def _parse_message(self, *, uid: str, raw_message: bytes, flags_line: str) -> ParsedMailMessage:
        message = BytesParser(policy=policy.default).parsebytes(raw_message)
        from_addresses = getaddresses(message.get_all("from", []))
        to_addresses = getaddresses(message.get_all("to", []))

        body_text = self._extract_body_text(message)
        snippet = (body_text or "").strip().replace("\r", " ").replace("\n", " ")
        if len(snippet) > 160:
            snippet = f"{snippet[:157]}..."

        sent_at = self._parse_datetime(message.get("date"))
        received_at = sent_at

        return ParsedMailMessage(
            remote_uid=uid,
            message_id=message.get("message-id"),
            subject=(message.get("subject") or "(No subject)").strip(),
            from_name=from_addresses[0][0] or None if from_addresses else None,
            from_address=from_addresses[0][1] or None if from_addresses else None,
            to_summary=", ".join(item[1] or item[0] for item in to_addresses[:4]) or None,
            snippet=snippet or None,
            body_text=body_text,
            is_read="\\Seen" in flags_line,
            sent_at=sent_at,
            received_at=received_at,
        )

    def _extract_body_text(self, message: EmailMessage) -> str | None:
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition", "")):
                    try:
                        return part.get_content().strip()
                    except Exception:
                        payload = part.get_payload(decode=True) or b""
                        charset = part.get_content_charset() or "utf-8"
                        return payload.decode(charset, errors="ignore").strip()
        try:
            return message.get_body(preferencelist=("plain",)).get_content().strip()  # type: ignore[union-attr]
        except Exception:
            payload = message.get_payload(decode=True)
            if isinstance(payload, bytes):
                charset = message.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="ignore").strip()
        return None

    def _parse_datetime(self, value: str | None) -> str | None:
        if not value:
            return None
        try:
            dt = parsedate_to_datetime(value)
        except Exception:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).isoformat()
