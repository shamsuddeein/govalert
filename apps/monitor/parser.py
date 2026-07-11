import re
import difflib
from bs4 import BeautifulSoup
from core.utils import sanitise_html

# Volume 3 Keyword Dictionary
HIGH_CONFIDENCE_TRIGGERS = [
    'recruitment', 'recruitment portal', 'application portal',
    'apply now', 'submit application', 'recruitment exercise',
    'vacancy announcement', 'job advertisement', 'employment opportunity',
    'application form', 'online registration', '2024/2025 recruitment',
    'recruitment into', 'exercise for the post of', 'eligible candidates'
]

MEDIUM_CONFIDENCE_TRIGGERS = [
    'portal', 'form', 'apply', 'candidate', 'shortlist',
    'requirements', 'qualifications', 'position', 'cadre',
    'officer', 'constable', 'officer cadet', 'batch'
]

DEADLINE_PATTERNS = [
    r'(?i)deadline[:\s]+(.{5,40})',
    r'(?i)closing date[:\s]+(.{5,40})',
    r'(?i)applications? close[s]? on (.{5,40})',
    r'(?i)submit (?:on or )?before (.{5,40})',
    r'\d{1,2}(?:st|nd|rd|th)? \w+ \d{4}',
    r'\d{1,2}/\d{1,2}/\d{4}',
    r'\d{4}-\d{2}-\d{2}',
]


def clean_html_to_text(html_content: str) -> str:
    """Normalize HTML by removing scripts, styles, navigation, footer, etc."""
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove unwanted tag elements
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript', 'iframe']):
        tag.decompose()

    # Locate main body content area
    main = soup.find('main') or soup.find('article') or soup.find('div', id='content') or soup.find('div', class_='content')
    if main:
        text = main.get_text(separator=' ')
    else:
        text = soup.get_text(separator=' ')

    return sanitise_html(text)


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
    Scan text content for recruitment triggers and attempt to extract deadlines/positions.
    Returns: { 'is_recruitment': bool, 'confidence': str, 'deadline': str, 'positions': str }
    """
    text_lower = text.lower()

    high_matches = [trig for trig in HIGH_CONFIDENCE_TRIGGERS if trig in text_lower]
    med_matches = [trig for trig in MEDIUM_CONFIDENCE_TRIGGERS if trig in text_lower]

    is_recruitment = len(high_matches) >= 2 or (len(high_matches) >= 1 and len(med_matches) >= 2)
    confidence = 'HIGH' if len(high_matches) >= 2 else ('MEDIUM' if len(high_matches) >= 1 or len(med_matches) >= 3 else 'LOW')

    # Extract deadline
    deadline = ''
    for pattern in DEADLINE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            deadline = match.group(1).strip() if match.groups() else match.group(0).strip()
            break

    # Extract position titles/roles
    positions_list = []
    sentences = re.split(r'[.!?\n]', text)
    for sent in sentences:
        sent_lower = sent.lower()
        if any(w in sent_lower for w in ['recruit', 'vacancy', 'position', 'post', 'hiring']):
            cleaned_sent = re.sub(r'\s+', ' ', sent).strip()
            if 15 < len(cleaned_sent) < 150:
                positions_list.append(cleaned_sent)
                if len(positions_list) >= 3:
                    break

    positions = '; '.join(positions_list) if positions_list else 'Multiple Positions'

    return {
        'is_recruitment': is_recruitment,
        'confidence': confidence,
        'deadline': deadline[:100] if deadline else 'Not Specified',
        'positions': positions[:250]
    }
