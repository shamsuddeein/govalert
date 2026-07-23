import logging
import uuid
from django.utils import timezone
from django.db import transaction, IntegrityError

from apps.alerts.models import Alert, AlertStatus, RecruitmentEvent, DecisionLog, EventStatus
from apps.detector.trust import calculate_trust_score
from apps.detector.ai import classify_recruitment_with_ai
from apps.notifications.tasks import dispatch_alert
from apps.alerts.fingerprint import generate_fingerprint, normalize_recruitment_data, detect_update
from core.utils import compute_content_hash

logger = logging.getLogger(__name__)


def supersede_older_alerts(alert: Alert) -> int:
    """
    Mark all older approved alerts sharing the same fingerprint (or agency & title)
    as SUPERSEDED so that only the latest active update is displayed to users.
    """
    if not alert:
        return 0

    qs = Alert.objects.exclude(id=alert.id).filter(status=AlertStatus.APPROVED)
    
    if alert.recruitment_event and alert.recruitment_event.fingerprint:
        qs = qs.filter(recruitment_event__fingerprint=alert.recruitment_event.fingerprint)
    elif alert.agency and alert.title:
        qs = qs.filter(agency=alert.agency, title=alert.title)
    else:
        return 0

    updated_count = qs.update(status=AlertStatus.SUPERSEDED)
    if updated_count > 0:
        logger.info(f"Marked {updated_count} older alert(s) as SUPERSEDED for alert {alert.id}.")
    return updated_count


def create_alert_from_scrape(portal, content, matched_data) -> Alert | None:
    """
    Analyze scraped content, calculate trust, run AI checks, and create alert.
    
    Uses fingerprint-based deduplication:
    - Generates SHA-256 fingerprint from title/deadline/positions/url/agency
    - Checks if fingerprint already exists
    - If exists: detects if it's an update (different deadline/positions) or duplicate
    - If duplicate: returns None (no alert)
    - If new or update: creates event, decision log, and alert
    - Only sends notifications for NEW events (not updates by default)
    """
    agency = portal.agency

    from apps.monitor.parser import clean_html_to_text
    if '<' in content and '>' in content:
        content = clean_html_to_text(content)

    # 1. Run AI classification
    is_fallback = False
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

        classification = 'UNCERTAIN'
        confidence = 40

        if has_fraud_keywords:
            classification = 'UNCERTAIN'
            confidence = 30
        elif not has_recruitment_keywords:
            classification = 'UNCERTAIN'
            confidence = 30

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
        is_fallback = True

    # 2. Calculate trust score
    ai_confidence = ai_res.get('confidence', 70)
    trust_score = calculate_trust_score(agency, portal.url, ai_confidence)

    # 3. Determine status
    # CRITICAL: All newly detected alerts from automated scrapers MUST start as PENDING.
    # Human review via /admin/alerts is mandatory to set status='APPROVED',
    # is_verified=True, verified_by=username, and verified_at=now.
    alert_status = AlertStatus.PENDING
    logger.info(f"Alert queued as PENDING for human admin review (trust_score={trust_score}).")

    # 4. Extract and normalize recruitment data
    from apps.monitor.parser import validate_and_sanitize_deadline
    extracted = ai_res.get('extracted', {})
    title = f"{agency.acronym} Recruitment Update Detected"
    # Prioritize matched_data (from scraper) over AI extraction, as it's more accurate
    raw_deadline = matched_data.get('deadline') or extracted.get('deadline') or ""
    deadline = validate_and_sanitize_deadline(raw_deadline)
    positions = matched_data.get('positions') or extracted.get('positions') or "Multiple Positions"
    
    # 5. Generate fingerprint for deduplication
    fingerprint = generate_fingerprint(
        title=title,
        deadline=deadline,
        positions=positions,
        url=portal.url,
        agency_name=agency.name
    )

    # 6. Check if fingerprint already exists (detects duplicates and updates)
    # The newest event is the current state of this recruitment's update chain.
    existing_event = RecruitmentEvent.objects.filter(fingerprint=fingerprint).order_by('-created_at').first()
    changes_dict = {}  # Track what changed for DecisionLog
    
    if existing_event:
        # Check if this is an update or just a duplicate
        is_update, changes_dict = detect_update(
            fingerprint,
            {'title': title, 'deadline': deadline, 'positions': positions},
            existing_event
        )
        
        if not is_update:
            logger.info(f"Duplicate recruitment ignored (fingerprint={fingerprint[:8]}...).")
            from django.core.cache import cache
            try:
                # Use a default 0 if key not set
                current_skipped = cache.get('metrics_duplicate_events_skipped')
                if current_skipped is None:
                    cache.set('metrics_duplicate_events_skipped', 1, timeout=None)
                else:
                    cache.incr('metrics_duplicate_events_skipped')
            except Exception as e:
                logger.warning(f"Failed to increment duplicate counter: {e}")
            return None
        
        # Preserve history: each meaningful change becomes a new event and Alert
        # linked to the prior state. This also gives notification deduplication a
        # new alert id for each update.
        logger.info(f"Recruitment updated (fingerprint={fingerprint[:8]}...). Creating update event and alert.")
        event_suffix = uuid.uuid4().hex[:6]
        rec_event = RecruitmentEvent.objects.create(
            event_id=f"evt_{timezone.now().strftime('%Y%m%d')}_{event_suffix}",
            fingerprint=fingerprint,
            status=EventStatus.UPDATED,
            previous_event=existing_event,
            portal=portal,
            event_type=ai_res.get('event_type') or 'RECRUITMENT_OPEN',
            content_hash=compute_content_hash(content),
            title=title,
            deadline=deadline,
            positions=positions,
        )
        event_status = EventStatus.UPDATED
    else:
        # New recruitment
        logger.info(f"New recruitment detected (fingerprint={fingerprint[:8]}...).")
        event_status = EventStatus.NEW
 
        # 7. Create RecruitmentEvent with fingerprint (atomic transaction for race condition safety)
        event_suffix = uuid.uuid4().hex[:6]
        event_id = f"evt_{timezone.now().strftime('%Y%m%d')}_{event_suffix}"
        content_hash = compute_content_hash(content)

        try:
            with transaction.atomic():
                rec_event = RecruitmentEvent.objects.create(
                    event_id=event_id,
                    fingerprint=fingerprint,
                    status=event_status,
                    previous_event=None,
                    portal=portal,
                    event_type=ai_res.get('event_type') or 'RECRUITMENT_OPEN',
                    content_hash=content_hash,
                    title=title,
                    deadline=deadline,
                    positions=positions,
                )
        except IntegrityError as e:
            logger.warning(f"IntegrityError creating event (race condition?): {e}. Event already exists.")
            return None
 
    # 8. Create or update DecisionLog
    rule_matches = matched_data.get('rule_matches', [])
    if not rule_matches:
        content_lower = content.lower()
        if 'apply' in content_lower:
            rule_matches.append('apply_keyword')
        if 'recruitment' in content_lower:
            rule_matches.append('recruitment_keyword')
        if 'careers' in content_lower:
            rule_matches.append('careers_keyword')

    decision_source = 'Rule Engine Fallback' if is_fallback else 'Gemini AI'
    DecisionLog.objects.update_or_create(
        event=rec_event,
        defaults={
            'rule_matches': rule_matches,
            'gemini_score': float(ai_confidence / 100.0),
            'final_trust': trust_score,
            'reason': f"{decision_source}: Classification: {ai_res.get('classification') or 'UNCERTAIN'}. Trust score matches calculated metrics.",
            'title': title,
            'deadline': deadline,
            'positions': positions,
            'changes': changes_dict,  # Will be empty dict for NEW events, or contain changes for UPDATED
        }
    )

    # 9. Create or update Alert
    requirements = extracted.get('requirements') or "Check website"

    alert, alert_created = Alert.objects.update_or_create(
        recruitment_event=rec_event,
        defaults={
            'agency': agency,
            'portal': portal,
            'event_type': ai_res.get('event_type') or 'RECRUITMENT_OPEN',
            'title': title,
            'positions': positions,
            'deadline': deadline,
            'requirements': requirements,
            'source_url': portal.url,
            'content_excerpt': content[:2000],
            'trust_score': trust_score,
            'ai_classification': ai_res.get('classification') or 'UNCERTAIN',
            'ai_confidence': ai_confidence,
            'ai_red_flags': ai_res.get('red_flags') or [],
            'status': alert_status,
        }
    )

    logger.info(f"Processed event {rec_event.event_id} (status={rec_event.status}) and alert {alert.id} (created={alert_created})")

    # Post event JSON to event channel
    try:
        from storage.events import write_event
        write_event(
            event_id=rec_event.event_id,
            event=rec_event.event_type,
            agency=agency.name,
            acronym=agency.acronym,
            category=agency.category,
            title=title,
            url=portal.url,
            trust_score=trust_score,
            deadline=deadline,
            positions=positions,
            content_hash=rec_event.content_hash,
            fingerprint=fingerprint,
            changes=changes_dict
        )
    except Exception as exc:
        logger.warning(f"Failed to post to event channel: {exc}")

    # Approval is intentionally a separate human action. The admin approval
    # endpoint dispatches both new openings and update events.
    if alert.status == AlertStatus.APPROVED:
        supersede_older_alerts(alert)
        if alert_created:
            dispatch_alert.delay(alert.id)

    return alert

