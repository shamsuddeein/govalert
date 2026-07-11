import logging
from apps.alerts.models import Alert, AlertStatus
from apps.detector.trust import calculate_trust_score
from apps.detector.ai import classify_recruitment_with_ai
from apps.notifications.tasks import dispatch_alert

logger = logging.getLogger(__name__)


def create_alert_from_scrape(portal, content, matched_data) -> Alert | None:
    """
    Analyze scraped content, calculate trust, run AI checks, and create alert.
    If alert is approved, triggers the notification dispatch.
    """
    agency = portal.agency

    # 1. Run AI classification
    try:
        ai_res = classify_recruitment_with_ai(agency.name, portal.url, content)
        if not ai_res:
            raise ValueError("AI returned empty classification response.")
    except Exception as exc:
        logger.warning(f"AI classification failed ({exc}). Falling back to Rule Engine.")
        # Rule-based fallback engine
        content_lower = content.lower()
        has_fraud_keywords = any(kw in content_lower for kw in ["fee", "pay", "charge", "naira", "deposit", "payment", "bank"])
        has_recruitment_keywords = any(kw in content_lower for kw in ["recruitment", "careers", "apply", "job", "vacancy"])

        classification = 'REAL'
        confidence = 75

        if has_fraud_keywords:
            classification = 'SUSPICIOUS'
            confidence = 80
        elif not has_recruitment_keywords:
            classification = 'UNCERTAIN'
            confidence = 50

        ai_res = {
            'classification': classification,
            'confidence': confidence,
            'event_type': 'RECRUITMENT_OPEN' if has_recruitment_keywords else 'OTHER',
            'red_flags': ['FRAUD_KEYWORDS_DETECTED'] if has_fraud_keywords else [],
            'extracted': {
                'positions': matched_data.get('positions') or "Multiple Positions",
                'deadline': matched_data.get('deadline') or "",
                'requirements': "Check website"
            }
        }

    # 2. Calculate trust score
    ai_confidence = ai_res.get('confidence', 70)
    trust_score = calculate_trust_score(agency, portal.url, ai_confidence)

    # 3. Determine status
    if trust_score >= 70:
        status = AlertStatus.APPROVED
    else:
        status = AlertStatus.PENDING

    extracted = ai_res.get('extracted', {})
    positions = extracted.get('positions') or matched_data.get('positions') or "Multiple Positions"
    deadline = extracted.get('deadline') or matched_data.get('deadline') or ""
    requirements = extracted.get('requirements') or "Check website"

    alert = Alert.objects.create(
        agency=agency,
        portal=portal,
        event_type=ai_res.get('event_type') or 'RECRUITMENT_OPEN',
        title=f"{agency.acronym} Recruitment Update Detected",
        positions=positions,
        deadline=deadline,
        requirements=requirements,
        source_url=portal.url,
        content_excerpt=content[:2000],
        trust_score=trust_score,
        ai_classification=ai_res.get('classification') or 'UNCERTAIN',
        ai_confidence=ai_confidence,
        ai_red_flags=ai_res.get('red_flags') or [],
        status=status
    )

    logger.info(f"Created alert {alert.id} status={alert.status} trust={alert.trust_score}")

    if alert.status == AlertStatus.APPROVED:
        dispatch_alert(alert.id)

    return alert
