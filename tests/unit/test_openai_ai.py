import pytest
from unittest.mock import patch
from apps.agencies.models import Agency
from apps.alerts.models import Alert, AlertStatus, EventType
from apps.detector.ai import (
    summarize_recruitment_with_openai,
    detect_scam_with_openai,
    verify_recruitment_with_openai,
    classify_recruitment_with_ai
)
from apps.detector.trust import calculate_trust_score


@pytest.mark.django_db
def test_openai_summarization():
    mock_res = {
        "summary_overview": "Official recruitment for Nigeria Police Force.",
        "key_positions": ["Constable"],
        "eligibility_criteria": ["SSCE"],
        "application_steps": ["Apply online"],
        "deadline_text": "30 August 2026",
        "fee_required": False
    }
    with patch('apps.detector.ai._call_openai', return_value=mock_res):
        res = summarize_recruitment_with_openai("NPF Constable Recruitment", "Nigeria Police Force", "NPF opens applications for 10,000 constables.")
        assert res["summary_overview"] == "Official recruitment for Nigeria Police Force."
        assert "Constable" in res["key_positions"]


@pytest.mark.django_db
def test_openai_scam_detection():
    mock_res = {
        "is_scam": True,
        "scam_risk_score": 85,
        "red_flags": ["Direct fee request via bank transfer"],
        "reasoning": "Notice asks applicants to pay N5000 processing fee."
    }
    with patch('apps.detector.ai._call_openai', return_value=mock_res):
        res = detect_scam_with_openai("Nigeria Customs Service", "http://customs-recruitment-fee.com", "Pay N5000 processing fee to 0123456789.")
        assert res["is_scam"] is True
        assert res["scam_risk_score"] == 85
        assert "Direct fee request" in res["red_flags"][0]


@pytest.mark.django_db
def test_openai_verification_assistance():
    mock_res = {
        "verification_status": "VERIFIED",
        "confidence_score": 95,
        "verification_factors": [
            {"label": "Domain Alignment", "passed": True},
            {"label": "No Fee Requirement", "passed": True}
        ],
        "notes": "Verified against official gazette."
    }
    with patch('apps.detector.ai._call_openai', return_value=mock_res):
        res = verify_recruitment_with_openai("Nigeria Immigration Service", "https://immigration.gov.ng", "Official NIS 2026 recruitment.")
        assert res["verification_status"] == "VERIFIED"
        assert res["confidence_score"] == 95


@pytest.mark.django_db
def test_enhanced_trust_score_with_scam_penalty():
    agency = Agency.objects.create(name="Federal Inland Revenue Service", acronym="FIRS", official_domains=["firs.gov.ng"])

    mock_scam = {
        "is_scam": True,
        "scam_risk_score": 90,
        "red_flags": ["Fake deposit requested"],
        "reasoning": "Fee scam detected"
    }
    with patch('apps.detector.ai._call_openai', return_value=mock_scam):
        score = calculate_trust_score(agency, "https://firs-fake-jobs.com", ai_confidence=90, content="Pay N10,000 application fee.")
        assert score < 30
