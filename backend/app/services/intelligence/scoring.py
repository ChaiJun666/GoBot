from __future__ import annotations

from app.schemas.lead import EnrichedLead, IntelligenceFactors, LeadIntelligence, ScrapedLead


class LeadIntelligenceScorer:
    def __init__(self) -> None:
        self._industry_scores = {
            "restaurant": {"potential": 85, "digital_readiness": 75, "urgency": 90},
            "automotive": {"potential": 90, "digital_readiness": 70, "urgency": 85},
            "retail": {"potential": 95, "digital_readiness": 80, "urgency": 95},
            "professional": {"potential": 80, "digital_readiness": 85, "urgency": 75},
            "healthcare": {"potential": 85, "digital_readiness": 65, "urgency": 80},
            "education": {"potential": 75, "digital_readiness": 70, "urgency": 85},
            "realestate": {"potential": 90, "digital_readiness": 75, "urgency": 80},
        }
        self._location_scores = {
            "jakarta": 95,
            "bandung": 80,
            "surabaya": 85,
            "medan": 75,
            "yogyakarta": 70,
            "jogja": 70,
            "default": 65,
        }

    def score_leads(self, leads: list[ScrapedLead], industry: str = "professional") -> list[EnrichedLead]:
        enriched: list[EnrichedLead] = []

        for lead in leads:
            factors = IntelligenceFactors(
                data_completeness=self._score_data_completeness(lead),
                business_quality=self._score_business_quality(lead),
                digital_presence=self._score_digital_presence(lead),
                location_value=self._score_location(lead),
                industry_potential=self._score_industry_potential(industry),
                contactability=self._score_contactability(lead),
            )
            score = round(
                (factors.data_completeness * 0.20)
                + (factors.business_quality * 0.25)
                + (factors.digital_presence * 0.15)
                + (factors.location_value * 0.15)
                + (factors.industry_potential * 0.15)
                + (factors.contactability * 0.10)
            )
            intelligence = LeadIntelligence(
                score=score,
                category=self._categorize_score(score),
                priority=self._priority(score),
                recommendation=self._recommendation(score),
                factors=factors,
            )
            enriched.append(
                EnrichedLead(
                    **lead.model_dump(),
                    intelligence=intelligence,
                )
            )

        enriched.sort(key=lambda item: item.intelligence.score, reverse=True)
        return enriched

    def summarize(self, leads: list[EnrichedLead]) -> dict[str, int]:
        if not leads:
            return {
                "total_leads": 0,
                "average_score": 0,
                "priority_leads": 0,
            }

        total_score = sum(lead.intelligence.score for lead in leads)
        priority_leads = sum(1 for lead in leads if lead.intelligence.priority == "HIGH")
        return {
            "total_leads": len(leads),
            "average_score": round(total_score / len(leads)),
            "priority_leads": priority_leads,
        }

    def _score_data_completeness(self, lead: ScrapedLead) -> int:
        score = 0
        if lead.name.strip():
            score += 25
        if lead.address.strip():
            score += 20
        if lead.phone:
            score += 20
        if lead.email:
            score += 15
        if lead.website:
            score += 15
        if lead.rating and self._parse_number(lead.rating) is not None:
            score += 10
        return min(score, 100)

    def _score_business_quality(self, lead: ScrapedLead) -> int:
        score = 50
        rating = self._parse_number(lead.rating)
        if rating is not None:
            if rating >= 4.5:
                score += 30
            elif rating >= 4.0:
                score += 20
            elif rating >= 3.5:
                score += 10
            elif rating < 3.0:
                score -= 10

        name = lead.name.lower()
        if any(token in name for token in ("official", "group", "center")):
            score += 10
        if len(name) > 30:
            score -= 5
        if len(name) < 5:
            score -= 10

        address = lead.address.lower()
        if "jl." in address or "jalan" in address:
            score += 5
        if any(token in address for token in ("jakarta", "bandung", "surabaya")):
            score += 5
        if any(token in address for token in ("mall", "plaza", "tower")):
            score += 10
        return min(max(score, 0), 100)

    def _score_digital_presence(self, lead: ScrapedLead) -> int:
        score = 20
        if lead.website:
            website = lead.website.lower()
            score += 40
            if ".com" in website or ".co.id" in website:
                score += 10
            if "instagram" in website or "facebook" in website:
                score += 5
            elif website.startswith("http"):
                score += 15
        if lead.phone:
            score += 15
        return min(score, 100)

    def _score_location(self, lead: ScrapedLead) -> int:
        address = lead.address.lower()
        if any(token in address for token in ("jakarta", "depok", "tangerang", "bekasi")):
            return self._location_scores["jakarta"]
        for token in ("bandung", "surabaya", "medan", "yogyakarta", "jogja"):
            if token in address:
                return self._location_scores[token]
        return self._location_scores["default"]

    def _score_industry_potential(self, industry: str) -> int:
        values = self._industry_scores.get(industry.lower())
        if values is None:
            return 70
        return round(
            (values["potential"] + values["digital_readiness"] + values["urgency"]) / 3
        )

    def _score_contactability(self, lead: ScrapedLead) -> int:
        score = 0
        if lead.phone:
            score += 50
            if lead.phone.startswith("08") or lead.phone.startswith("+62"):
                score += 20
        if lead.email:
            score += 30
        if lead.website:
            score += 10
        return min(score, 100)

    def _categorize_score(self, score: int) -> str:
        if score >= 85:
            return "A+ (Excellent)"
        if score >= 75:
            return "A (High Quality)"
        if score >= 65:
            return "B (Good)"
        if score >= 55:
            return "C (Average)"
        return "D (Low Priority)"

    def _priority(self, score: int) -> str:
        if score >= 85:
            return "HIGH"
        if score >= 65:
            return "MEDIUM"
        return "LOW"

    def _recommendation(self, score: int) -> str:
        if score >= 85:
            return "Priority lead - contact immediately with premium approach"
        if score >= 75:
            return "High-value lead - personalized outreach recommended"
        if score >= 65:
            return "Good prospect - standard campaign approach"
        if score >= 55:
            return "Qualified lead - nurture with content"
        return "Low priority - minimal resource allocation"

    def _parse_number(self, value: str | None) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except ValueError:
            return None
