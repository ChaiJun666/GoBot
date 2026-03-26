from __future__ import annotations

from app.schemas.mail import MailProviderConfig, MailProviderKey


MAIL_PROVIDER_CONFIGS: dict[MailProviderKey, MailProviderConfig] = {
    MailProviderKey.NETEASE_163: MailProviderConfig(
        key=MailProviderKey.NETEASE_163,
        label="163.com",
        imap_host="imap.163.com",
        imap_port=993,
        smtp_host="smtp.163.com",
        smtp_port=465,
        smtp_starttls=False,
    ),
    MailProviderKey.NETEASE_163_VIP: MailProviderConfig(
        key=MailProviderKey.NETEASE_163_VIP,
        label="vip.163.com",
        imap_host="imap.vip.163.com",
        imap_port=993,
        smtp_host="smtp.vip.163.com",
        smtp_port=465,
        smtp_starttls=False,
    ),
    MailProviderKey.NETEASE_126: MailProviderConfig(
        key=MailProviderKey.NETEASE_126,
        label="126.com",
        imap_host="imap.126.com",
        imap_port=993,
        smtp_host="smtp.126.com",
        smtp_port=465,
        smtp_starttls=False,
    ),
    MailProviderKey.NETEASE_126_VIP: MailProviderConfig(
        key=MailProviderKey.NETEASE_126_VIP,
        label="vip.126.com",
        imap_host="imap.vip.126.com",
        imap_port=993,
        smtp_host="smtp.vip.126.com",
        smtp_port=465,
        smtp_starttls=False,
    ),
    MailProviderKey.NETEASE_188: MailProviderConfig(
        key=MailProviderKey.NETEASE_188,
        label="188.com",
        imap_host="imap.188.com",
        imap_port=993,
        smtp_host="smtp.188.com",
        smtp_port=465,
        smtp_starttls=False,
    ),
    MailProviderKey.NETEASE_188_VIP: MailProviderConfig(
        key=MailProviderKey.NETEASE_188_VIP,
        label="vip.188.com",
        imap_host="imap.vip.188.com",
        imap_port=993,
        smtp_host="smtp.vip.188.com",
        smtp_port=465,
        smtp_starttls=False,
    ),
    MailProviderKey.YEAH: MailProviderConfig(
        key=MailProviderKey.YEAH,
        label="yeah.net",
        imap_host="imap.yeah.net",
        imap_port=993,
        smtp_host="smtp.yeah.net",
        smtp_port=465,
        smtp_starttls=False,
    ),
    MailProviderKey.GMAIL: MailProviderConfig(
        key=MailProviderKey.GMAIL,
        label="Gmail",
        imap_host="imap.gmail.com",
        imap_port=993,
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_starttls=True,
    ),
    MailProviderKey.OUTLOOK: MailProviderConfig(
        key=MailProviderKey.OUTLOOK,
        label="Outlook",
        imap_host="outlook.office365.com",
        imap_port=993,
        smtp_host="smtp.office365.com",
        smtp_port=587,
        smtp_starttls=True,
    ),
    MailProviderKey.QQ: MailProviderConfig(
        key=MailProviderKey.QQ,
        label="QQ Mail",
        imap_host="imap.qq.com",
        imap_port=993,
        smtp_host="smtp.qq.com",
        smtp_port=587,
        smtp_starttls=True,
    ),
}


def list_provider_configs() -> list[MailProviderConfig]:
    return list(MAIL_PROVIDER_CONFIGS.values())
