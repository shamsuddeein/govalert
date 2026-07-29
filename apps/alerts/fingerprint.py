"""
Fingerprint-based recruitment deduplication.
Generates deterministic hashes of recruitment identifying data to detect duplicates and updates.
"""
import hashlib
import logging
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)


def normalize_recruitment_data(
    title: str,
    deadline: str,
    positions: str,
    url: str,
    agency_name: str
) -> Dict[str, str]:
    """
    Normalize recruitment data before hashing.
    Removes formatting differences that shouldn't cause duplicate alerts.
    """
    # Strip, lowercase, remove extra whitespace
    title = ' '.join(title.strip().lower().split())
    deadline = deadline.strip()
    url = url.split('?')[0].split('#')[0]  # Remove query params and fragments
    agency_name = agency_name.strip()
    
    # Normalize positions: split, clean, sort, rejoin
    if positions:
        pos_list = [p.strip().lower() for p in positions.split(',') if p.strip()]
        pos_list.sort()
        positions = ','.join(pos_list)
    
    return {
        'title': title,
        'deadline': deadline,
        'positions': positions,
        'url': url,
        'agency': agency_name,
    }


def generate_fingerprint(
    title: str,
    deadline: str,
    positions: str,
    url: str,
    agency_name: str
) -> str:
    """
    Generate a deterministic SHA-256 fingerprint from CORE recruitment identifying data.
    Includes: agency, title, url.
    Deliberately EXCLUDES: deadline and positions.

    Exclusion rationale:
    - Deadline changes (extensions) should produce update events, not new recruitments.
    - Position changes (more roles added) should produce update events too.
    Both fields are tracked in detect_update() for change detection.

    Note: two different agencies posting identical job titles at the same URL
    will share a fingerprint. This is acceptable — the URL itself should be
    unique per agency's recruitment portal.

    Returns 64-character hex string.
    """
    normalized = normalize_recruitment_data(title, deadline, positions, url, agency_name)
    
    # Fingerprint only contains immutable recruitment identity fields. Deadline and
    # positions are deliberately excluded so either can produce an update event.
    payload = f"""agency={normalized['agency']}
title={normalized['title']}
url={normalized['url']}"""
    
    fingerprint = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    logger.debug(f"Generated fingerprint: {fingerprint}")
    return fingerprint


def _classify_deadline_change(old_deadline: str, new_deadline: str) -> str:
    """
    Determine whether a deadline change represents an extension (moved to a later date)
    or just a change (different but not necessarily later).

    Parses both strings as dates; falls back to 'deadline_changed' if parsing fails.
    Fixes the old string-length heuristic which misclassified e.g.
    '31 March 2026' (14 chars) > '1 April 2027' (13 chars) as an extension.
    """
    from dateutil import parser as date_parser
    try:
        old_dt = date_parser.parse(old_deadline, dayfirst=True)
        new_dt = date_parser.parse(new_deadline, dayfirst=True)
        return 'deadline_extended' if new_dt > old_dt else 'deadline_changed'
    except Exception:
        # Cannot parse as date — fall back to a neutral label
        return 'deadline_changed'


def _is_unspecified_deadline(d: str) -> bool:
    if not d:
        return True
    clean = d.strip().lower()
    return clean in ['not specified', 'check website', 'n/a', 'none', '']


def detect_update(
    new_fingerprint: str,
    new_data: Dict[str, Any],
    existing_event: 'RecruitmentEvent'
) -> Tuple[bool, Dict[str, Any]]:
    """
    Detect if this is an update to an existing recruitment.
    
    Returns:
        (is_update: bool, changes: dict)
    
    Logic:
    - If same fingerprint AND same details → duplicate (no update)
    - If same fingerprint BUT different deadline/positions/title → update
    
    Examples:
        - Same recruitment, same details → (False, {})
        - Same recruitment, deadline changed → (True, {'deadline': {...}})
        - Same recruitment, positions changed → (True, {'positions': {...}})
    """
    changes = {}
    
    # Check deadline (can change - deadline extended, etc)
    new_deadline = new_data.get('deadline', '')
    old_deadline = existing_event.deadline or ''

    if new_deadline and new_deadline != old_deadline:
        # Ignore if new_deadline is unspecified/empty while old_deadline is valid
        if not _is_unspecified_deadline(old_deadline) and _is_unspecified_deadline(new_deadline):
            logger.debug(f"Ignoring deadline flap to unspecified ('{new_deadline}') over valid old deadline ('{old_deadline}').")
        else:
            changes['deadline'] = {
                'old': old_deadline,
                'new': new_deadline,
                'type': _classify_deadline_change(old_deadline, new_deadline),
            }
    
    # Check positions (can change - more positions added, etc)
    new_positions = new_data.get('positions', '')
    if new_positions and new_positions != existing_event.positions:
        changes['positions'] = {
            'old': existing_event.positions,
            'new': new_positions,
            'type': 'positions_added' if (new_positions.count(',') > existing_event.positions.count(',')) else 'positions_changed'
        }
    
    # Check title (rarely changes, but record if it does)
    new_title = new_data.get('title', '')
    if new_title and new_title != existing_event.title:
        changes['title'] = {
            'old': existing_event.title,
            'new': new_title,
        }
    
    is_update = len(changes) > 0
    return is_update, changes
