import re
import difflib
import logging
import warnings
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from core.utils import sanitise_html

logger = logging.getLogger(__name__)

# ─── Recruitment Keyword Dictionaries ─────────────────────────────────────────
# NOTE: Do NOT hardcode specific years (e.g. "2024/2025 recruitment") — those
# expire and silently stop matching. Use year-agnostic patterns instead.

HIGH_CONFIDENCE_TRIGGERS = [
    # Direct recruitment intent
    'recruitment', 'recruitment portal', 'application portal',
    'apply now', 'submit application', 'recruitment exercise',
    'vacancy announcement', 'job advertisement', 'employment opportunity',
    'application form', 'online registration',
    # Year-agnostic patterns (replaces old "2024/2025 recruitment")
    'recruitment exercise', 'recruitment into', 'exercise for the post of',
    'eligible candidates', 'eligible applicants',
    # Nigerian-specific phrasing
    'applications are invited', 'invitation for applications',
    'vacancies exist', 'seeks to recruit', 'is recruiting',
    'open for recruitment', 'commence recruitment', 'recruitment commences',
    'portal is open', 'portal now open', 'application window',
    'shortlisting exercise', 'written examination',
    # Military / paramilitary specific
    'enlistment', 'commission into', 'intake exercise',
    'new intake', 'recruitment of', 'cadet recruitment',
    'officer cadet application',
    # Civil service specific
    'federal civil service', 'public service', 'career opportunities',
    'job openings', 'career opening',
]

MEDIUM_CONFIDENCE_TRIGGERS = [
    'portal', 'form', 'apply', 'candidate', 'shortlist',
    'requirements', 'qualifications', 'position', 'cadre',
    'officer', 'constable', 'officer cadet', 'batch',
    'screening', 'interview', 'aptitude test', 'physical fitness',
    'passport photograph', 'o level', 'o\u2019level', 'ssce', 'waec', 'neco',
    'minimum qualification', 'age limit', 'between the ages',
    'years of experience', 'bsc', 'hnd', 'ond', 'nd', 'degree', 'certificate',
    'application fee', 'no application fee', 'free of charge',
    'closing date', 'deadline', 'before the closing',
    'submit online', 'complete the form', 'fill the form',
]

# Patterns that, if matched, should be treated as NEGATIVE signals
# (noise changes that are definitely not recruitment).
NOISE_PATTERNS = [
    r'cookie', r'privacy policy', r'javascript', r'stylesheet',
    r'google analytics', r'social media', r'follow us', r'subscribe to',
]

MONTH_PATTERN = r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)'

DEADLINE_PATTERNS = [
    r'(?i)deadline[:\s]+(.{5,60})',
    r'(?i)closing date[:\s]+(.{5,60})',
    r'(?i)applications?\s+close[s]?\s+on\s+(.{5,60})',
    r'(?i)submit\s+(?:on\s+or\s+)?before\s+(.{5,60})',
    r'(?i)on\s+or\s+before\s+(.{5,60})',
    r'(?i)not\s+later\s+than\s+(.{5,60})',
    # Nigerian date formats (strictly matching month names instead of \w+)
    rf'\b\d{{1,2}}(?:st|nd|rd|th)?\s+{MONTH_PATTERN}\s+\d{{4}}\b',
    rf'\b{MONTH_PATTERN}\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}\b',
    r'\b\d{1,2}/\d{1,2}/\d{4}\b',
    r'\b\d{4}-\d{2}-\d{2}\b',
]


def validate_and_sanitize_deadline(deadline_str: str) -> str:
    """
    Sanitize and validate an extracted deadline string.
    
    1. Rejects invalid non-date patterns (e.g. "31 of 1993").
    2. Rejects deadlines with years prior to the current year (e.g. 2024 when current year is 2026).
    3. Normalizes and caps length.
    """
    if not deadline_str or not isinstance(deadline_str, str):
        return "Not Specified"

    deadline_str = deadline_str.strip()
    if deadline_str.lower() in ["not specified", "check portal", "check website", "n/a", "none"]:
        return "Not Specified"

    import datetime
    current_year = datetime.datetime.now().year

    # Check for 4-digit years in the string
    years_found = [int(y) for y in re.findall(r'\b(19\d\d|20\d\d)\b', deadline_str)]
    if years_found:
        # If all mentioned years are in the past (< current_year), discard as expired date
        if max(years_found) < current_year:
            logger.info(f"Ignoring expired deadline '{deadline_str}' (year {max(years_found)} < current year {current_year}).")
            return "Not Specified"

    # Reject strings like "31 of 1993" or generic non-dates
    has_letters = bool(re.search(r'[a-zA-Z]', deadline_str))
    if has_letters:
        has_month = bool(re.search(MONTH_PATTERN, deadline_str, re.IGNORECASE))
        relative_match = re.search(r'\b\d+\s+(?:days?|weeks?|months?)\b', deadline_str, re.IGNORECASE)
        if not has_month and not relative_match:
            return "Not Specified"

    # Truncate clean whitespace
    cleaned = re.sub(r'\s+', ' ', deadline_str).strip()
    return cleaned[:80] if len(cleaned) >= 5 else "Not Specified"


def clean_html_to_text(html_content: str, content_type: str = '') -> str:
    """Normalize HTML by removing scripts, styles, navigation, footer, etc."""
    if not html_content:
        return ""

    # Sanitize NUL bytes
    html_content = html_content.replace('\x00', '')

    if not isinstance(content_type, str):
        content_type = str(content_type)

    # Check Content-Type header if provided
    if content_type and not any(ct in content_type.lower() for ct in ['text/html', 'application/xhtml+xml', 'text/plain']):
        logger.warning(f"non-HTML content ({content_type}), skipping parse")
        return sanitise_html(html_content[:5000])

    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=MarkupResemblesLocatorWarning)
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove unwanted tag elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript', 'iframe']):
                tag.decompose()

            # Locate main body content area
            main = (
                soup.find('main') or
                soup.find('article') or
                soup.find('div', id='content') or
                soup.find('div', class_='content')
            )
            if main:
                text = main.get_text(separator=' ')
            else:
                text = soup.get_text(separator=' ')

            return sanitise_html(text.replace('\x00', ''))
        except Exception as exc:
            logger.warning(f"BeautifulSoup parsing failed ({exc}), skipping parse")
            return sanitise_html(html_content[:5000].replace('\x00', ''))


def analyze_diff(old_text: str, new_text: str) -> str:
    """Identify added lines of text between two snapshots."""
    old_lines = [line.strip() for line in old_text.splitlines() if line.strip()]
    new_lines = [line.strip() for line in new_text.splitlines() if line.strip()]

    differ = difflib.Differ()
    diff = list(differ.compare(old_lines, new_lines))

    added_lines = [line[2:] for line in diff if line.startswith('+ ')]
    return '\n'.join(added_lines)


def match_recruitment_keywords(text: str) -> dict:
    """
    Scan text content for recruitment triggers and extract deadlines/positions.

    Scoring logic:
    - HIGH confidence: 2+ high triggers, OR 1 high + 2+ medium triggers.
    - MEDIUM confidence: 1 high trigger, OR 3+ medium triggers.
    - LOW confidence: everything else.

    Noise filtering: if the added text is dominated by tracking scripts,
    cookie notices, or social media widgets, suppress the match.

    Returns:
        {
            'is_recruitment': bool,
            'confidence': str ('HIGH' | 'MEDIUM' | 'LOW'),
            'deadline': str,
            'positions': str,
            'rule_matches': list[str],
        }
    """
    text_lower = text.lower()

    # Early noise filter: if the diff is noise-dominated, skip matching.
    noise_count = sum(1 for p in NOISE_PATTERNS if re.search(p, text_lower))
    word_count = len(text.split())
    if noise_count >= 3 and word_count < 150:
        return {
            'is_recruitment': False,
            'confidence': 'LOW',
            'deadline': 'Not Specified',
            'positions': 'Multiple Positions',
            'rule_matches': [],
        }

    high_matches = [trig for trig in HIGH_CONFIDENCE_TRIGGERS if trig in text_lower]
    med_matches = [trig for trig in MEDIUM_CONFIDENCE_TRIGGERS if trig in text_lower]

    is_recruitment = len(high_matches) >= 2 or (len(high_matches) >= 1 and len(med_matches) >= 2)

    if len(high_matches) >= 2:
        confidence = 'HIGH'
    elif len(high_matches) >= 1 or len(med_matches) >= 3:
        confidence = 'MEDIUM'
    else:
        confidence = 'LOW'

    # Extract deadline
    raw_deadline = ''
    for pattern in DEADLINE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_deadline = match.group(1).strip() if match.groups() else match.group(0).strip()
            break

    # Sanitize and validate deadline
    deadline = validate_and_sanitize_deadline(raw_deadline)

    # Extract position titles/roles
    positions_list = []
    sentences = re.split(r'[.!?\n]', text)
    for sent in sentences:
        sent_lower = sent.lower()
        if any(w in sent_lower for w in ['recruit', 'vacancy', 'position', 'post', 'hiring', 'enlist', 'commission']):
            cleaned_sent = re.sub(r'\s+', ' ', sent).strip()
            if 15 < len(cleaned_sent) < 200:
                positions_list.append(cleaned_sent)
                if len(positions_list) >= 3:
                    break

    positions = '; '.join(positions_list) if positions_list else 'Multiple Positions'

    return {
        'is_recruitment': is_recruitment,
        'confidence': confidence,
        'deadline': deadline,
        'positions': positions[:250],
        'rule_matches': high_matches + med_matches,
    }

