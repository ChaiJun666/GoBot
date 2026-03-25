from __future__ import annotations

from app.schemas.lead import ScrapedLead
from app.services.intelligence.scoring import LeadIntelligenceScorer


def test_intelligence_scores_and_prioritizes_leads() -> None:
    scorer = LeadIntelligenceScorer()
    leads = [
        ScrapedLead(
            name="Cafe Prime",
            address="Jl. Sudirman, Jakarta",
            phone="08123456789",
            website="https://cafeprime.example",
            rating="4.8",
        ),
        ScrapedLead(
            name="Warung",
            address="Bandung",
            phone=None,
            website=None,
            rating="3.2",
        ),
    ]

    scored = scorer.score_leads(leads, industry="restaurant")
    summary = scorer.summarize(scored)

    assert len(scored) == 2
    assert scored[0].intelligence.score >= scored[1].intelligence.score
    assert summary["total_leads"] == 2
    assert summary["average_score"] > 0
