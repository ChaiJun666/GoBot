from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx

from app.core.database import Database
from app.schemas.email_outreach import (
    GenerateEmailsRequest,
    GeneratedEmail,
    GenerateEmailsResponse,
    LeadOutreachSummary,
    OUTREACH_STAGE_FOLLOW_UP_DAYS,
    OUTREACH_STAGE_LABELS,
    OutreachStage,
    SendEmailItem,
    SendEmailsResponse,
    SendEmailResult,
    UpdateLeadStageRequest,
)
from app.schemas.mail import SendMailRequest
from app.services.llm.service import LlmConfigService
from app.services.mail.service import MailService

_CHINESE_LOCATION_KEYWORDS = (
    "china", "beijing", "shanghai", "guangzhou", "shenzhen", "hangzhou",
    "chengdu", "wuhan", "nanjing", "suzhou", "xiamen", "ningbo",
    "dongguan", "foshan", "qingdao", "dalian", "tianjin", "chongqing",
    "zhengzhou", "changsha", "kunming", "hefei", "jinan", "fuzhou",
    "中国", "北京", "上海", "广州", "深圳", "杭州", "成都", "武汉",
    "南京", "苏州", "厦门", "宁波", "东莞", "佛山", "青岛", "大连",
)

_STAGE_PROMPTS: dict[OutreachStage, str] = {
    OutreachStage.INITIAL_OUTREACH: (
        "You are a professional B2B outreach specialist writing a FIRST-CONTACT email. "
        "Your goal is to establish awareness and introduce yourself / your company. "
        "Be warm, concise, and mention the lead's company or industry to show genuine interest. "
        "Include a clear but soft call-to-action (e.g. a quick chat or reply). "
        "Keep the body to 150-250 words."
    ),
    OutreachStage.INTEREST_CHECK: (
        "You are a B2B sales specialist writing a FOLLOW-UP email after initial outreach. "
        "Your goal is to check whether the lead is interested. "
        "Reference the previous email naturally, offer value (insight, case study, or resource), "
        "and ask a simple yes/no or low-commitment question. "
        "Keep the body to 100-200 words."
    ),
    OutreachStage.NEEDS_DISCOVERY: (
        "You are a B2B sales specialist writing a NEEDS-DISCOVERY email. "
        "The lead has shown some interest. Now dig deeper into their pain points and needs. "
        "Ask 1-2 targeted questions about their challenges. Share a brief relevant insight. "
        "Keep the body to 150-250 words."
    ),
    OutreachStage.PROPOSAL: (
        "You are a B2B sales specialist writing a PROPOSAL email. "
        "Based on previous conversations, present a tailored solution or offer. "
        "Be specific about benefits, timeline, and next steps. Include a clear call-to-action. "
        "Keep the body to 200-300 words."
    ),
    OutreachStage.CLOSING: (
        "You are a B2B sales specialist writing a CLOSING email. "
        "The lead is close to making a decision. Create gentle urgency, address any remaining concerns, "
        "and propose a concrete next step (call, meeting, contract). "
        "Keep the body to 150-250 words."
    ),
}

_SEMAPHORE_LIMIT = 5


class EmailGeneratorService:
    def __init__(
        self,
        *,
        database: Database,
        llm_config_service: LlmConfigService,
        mail_service: MailService,
    ) -> None:
        self._db = database
        self._llm_service = llm_config_service
        self._mail_service = mail_service

    def list_outreach_leads(
        self,
        *,
        campaign_id: str | None = None,
        stage: int | None = None,
    ) -> list[LeadOutreachSummary]:
        campaigns = self._db.list_campaigns(limit=200)
        stage_records = {
            rec["lead_id"]: rec for rec in self._db.list_lead_stages(campaign_id=campaign_id, stage=stage)
        }
        results: list[LeadOutreachSummary] = []
        for campaign in campaigns:
            if campaign_id and campaign["id"] != campaign_id:
                continue
            for lead in campaign["results"]:
                if not lead.email:
                    continue
                stage_rec = stage_records.get(lead.id)
                if stage_rec:
                    rec = dict(stage_rec)
                    rec["campaign_name"] = campaign["name"]
                    results.append(LeadOutreachSummary.from_record(rec))
                else:
                    results.append(LeadOutreachSummary(
                        id=f'{campaign["id"]}:{lead.email}',
                        lead_id=lead.id,
                        lead_email=lead.email,
                        lead_name=lead.name,
                        lead_company=lead.current_company or None,
                        lead_industry=campaign.get("industry"),
                        lead_location=campaign.get("location"),
                        lead_source=lead.source,
                        lead_headline=lead.headline or None,
                        campaign_id=campaign["id"],
                        campaign_name=campaign["name"],
                        current_stage=1,
                        emails_sent=0,
                        language="auto",
                        manual_override=False,
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC),
                    ))
        return results

    def update_lead_stage(
        self,
        lead_id: str,
        payload: UpdateLeadStageRequest,
    ) -> LeadOutreachSummary:
        record = self._db.get_lead_stage(lead_id)
        if record is None:
            raise LookupError(f"Lead stage record not found for lead_id={lead_id}")
        self._db.update_lead_stage(
            record["id"],
            current_stage=payload.stage,
            manual_override=1 if payload.manual_override else 0,
        )
        updated = self._db.get_lead_stage(lead_id)
        if updated is None:
            raise RuntimeError("Failed to retrieve updated lead stage")
        return LeadOutreachSummary.from_record(updated)

    async def generate_emails(self, payload: GenerateEmailsRequest) -> GenerateEmailsResponse:
        active_config = self._llm_service.get_active_config()
        if active_config is None:
            raise RuntimeError("No active LLM configuration. Please activate one in the LLM settings.")

        leads = self.list_outreach_leads()
        lead_map = {lead.lead_id: lead for lead in leads}
        target_ids = [lid for lid in payload.lead_ids if lid in lead_map]
        if not target_ids:
            raise LookupError("None of the specified lead_ids were found")

        sem = asyncio.Semaphore(_SEMAPHORE_LIMIT)
        emails: list[GeneratedEmail] = []
        errors: list[dict] = []

        async def _generate_one(lead_id: str) -> None:
            async with sem:
                lead = lead_map[lead_id]
                stage = OutreachStage(payload.stage or lead.current_stage)
                language = payload.language or lead.language
                if language == "auto":
                    language = self._detect_language(lead.lead_location)
                history = self._get_recent_email_summaries(lead.lead_email)
                prompt = self._build_prompt(stage, lead, history, language, payload.user_instructions)
                try:
                    result = await self._call_llm(active_config, prompt)
                    emails.append(GeneratedEmail(lead_id=lead_id, subject=result["subject"], body=result["body"]))
                except Exception as exc:
                    errors.append({"lead_id": lead_id, "error": str(exc)})

        await asyncio.gather(*[_generate_one(lid) for lid in target_ids])
        return GenerateEmailsResponse(emails=emails, errors=errors)

    def send_emails(self, payload: list[SendEmailItem]) -> SendEmailsResponse:
        results: list[SendEmailResult] = []
        for item in payload:
            try:
                lead_stage = self._db.get_lead_stage(item.lead_id)
                lead_email = lead_stage["lead_email"] if lead_stage else None
                if not lead_email:
                    lead = self._find_lead_email(item.lead_id)
                    lead_email = lead
                if not lead_email:
                    results.append(SendEmailResult(lead_id=item.lead_id, status="error", error="Lead has no email"))
                    continue

                self._mail_service.send_mail(SendMailRequest(
                    mailbox_id=item.mailbox_id,
                    to=[lead_email],
                    subject=item.subject,
                    body=item.body,
                ))

                now_iso = datetime.now(UTC).isoformat()
                if lead_stage:
                    new_emails_sent = lead_stage["emails_sent"] + 1
                    new_stage = lead_stage["current_stage"]
                    if not lead_stage["manual_override"]:
                        new_stage = min(new_emails_sent + 1, 5)
                    follow_up_days = OUTREACH_STAGE_FOLLOW_UP_DAYS.get(
                        OutreachStage(new_stage), 3
                    )
                    next_stage_at = (datetime.now(UTC) + timedelta(days=follow_up_days)).isoformat()
                    self._db.update_lead_stage(
                        lead_stage["id"],
                        current_stage=new_stage,
                        emails_sent=new_emails_sent,
                        last_email_at=now_iso,
                        next_stage_at=next_stage_at,
                        manual_override=0,
                        updated_at=now_iso,
                    )

                results.append(SendEmailResult(lead_id=item.lead_id, status="sent"))
            except Exception as exc:
                results.append(SendEmailResult(lead_id=item.lead_id, status="error", error=str(exc)))

        return SendEmailsResponse(results=results)

    def get_lead_history(self, lead_id: str) -> dict:
        stage = self._db.get_lead_stage(lead_id)
        if stage is None:
            raise LookupError(f"No stage record for lead_id={lead_id}")
        lead_email = stage["lead_email"]
        mailbox_id = stage.get("campaign_id")
        messages = []
        for mailbox in self._mail_service.list_mailboxes():
            for folder in ("sent", "inbox"):
                msgs = self._db.list_mail_messages(
                    mailbox_id=mailbox.id, folder=folder, limit=50,
                )
                for msg in msgs:
                    if msg.get("from_address") == lead_email or lead_email in (msg.get("to_summary") or ""):
                        messages.append(msg)
        messages.sort(key=lambda m: m.get("sent_at") or m.get("received_at") or "", reverse=True)
        return {
            "lead_id": lead_id,
            "lead_name": stage["lead_name"],
            "messages": messages[:20],
        }

    def ensure_lead_stages_for_campaign(self, campaign_id: str) -> int:
        campaign = self._db.get_campaign(campaign_id)
        if campaign is None:
            raise LookupError(f"Campaign {campaign_id} not found")
        created = 0
        for lead in campaign["results"]:
            if not lead.email:
                continue
            existing = self._db.get_lead_stage(lead.id)
            if existing:
                continue
            self._db.upsert_lead_stage(
                record_id=uuid4().hex,
                lead_id=lead.id,
                lead_email=lead.email,
                lead_name=lead.name,
                lead_company=lead.current_company or None,
                lead_industry=campaign.get("industry"),
                lead_location=campaign.get("location"),
                lead_source=lead.source,
                lead_headline=lead.headline or None,
                campaign_id=campaign_id,
                current_stage=1,
                emails_sent=0,
                language="auto",
            )
            created += 1
        return created

    def _detect_language(self, location: str | None) -> str:
        if not location:
            return "en"
        lower = location.lower()
        for keyword in _CHINESE_LOCATION_KEYWORDS:
            if keyword in lower:
                return "zh"
        return "en"

    def _get_recent_email_summaries(self, lead_email: str) -> list[str]:
        summaries: list[str] = []
        for mailbox in self._mail_service.list_mailboxes():
            for folder in ("sent",):
                msgs = self._db.list_mail_messages(
                    mailbox_id=mailbox.id, folder=folder, limit=20,
                )
                for msg in msgs:
                    if lead_email in (msg.get("to_summary") or ""):
                        summaries.append(msg.get("subject", "(No subject)"))
        return summaries[:3]

    def _build_prompt(
        self,
        stage: OutreachStage,
        lead: LeadOutreachSummary,
        history: list[str],
        language: str,
        user_instructions: str | None,
    ) -> str:
        stage_info = OUTREACH_STAGE_LABELS[stage]
        stage_name = stage_info.get("en", "Outreach")
        system_prompt = _STAGE_PROMPTS[stage]

        lang_label = "Chinese (Simplified)" if language == "zh" else "English"

        history_text = ""
        if history:
            history_text = "Previous emails sent:\n" + "\n".join(f"- {s}" for s in history)

        user_instructions_text = ""
        if user_instructions:
            user_instructions_text = f"\nAdditional user instructions:\n{user_instructions}"

        user_prompt = (
            f"Lead information:\n"
            f"- Name: {lead.lead_name}\n"
            f"- Company: {lead.lead_company or 'Unknown'}\n"
            f"- Industry: {lead.lead_industry or 'Unknown'}\n"
            f"- Location: {lead.lead_location or 'Unknown'}\n"
            f"- Source: {lead.lead_source or 'Unknown'}\n"
            f"- Headline: {lead.lead_headline or 'N/A'}\n\n"
            f"Stage: {stage_name} (stage {stage.value} of 5)\n\n"
            f"{history_text}\n\n"
            f"Requirements:\n"
            f"- Write in {lang_label}\n"
            f"- Subject line: concise and compelling (max 80 characters)\n"
            f"- Body: professional but warm tone\n"
            f"- Personalize based on the lead information\n"
            f"{user_instructions_text}\n\n"
            f"Return a JSON object with exactly two fields: {{\"subject\": \"...\", \"body\": \"...\"}}"
        )

        return f"{system_prompt}\n\n---\n\n{user_prompt}"

    async def _call_llm(self, config, prompt: str) -> dict[str, str]:
        url = f"{config.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": config.model_name,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 1024,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        # Try to extract JSON from the response
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON within markdown code blocks
            import re
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            # Last resort: try to find any JSON object
            match = re.search(r"\{[^{}]*\"subject\"[^{}]*\"body\"[^{}]*\}", content, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise RuntimeError(f"LLM response is not valid JSON: {content[:200]}")

    def _find_lead_email(self, lead_id: str) -> str | None:
        campaigns = self._db.list_campaigns(limit=200)
        for campaign in campaigns:
            for lead in campaign["results"]:
                if lead.id == lead_id:
                    return lead.email
        return None
