import json
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def classify_recruitment_with_ai(agency_name: str, url: str, content: str) -> dict:
    """
    Call Gemini Flash API to classify the recruitment change text.
    Returns: structured dict with classification status.
    """
    from apps.monitor.parser import clean_html_to_text
    if '<' in content and '>' in content:
        content = clean_html_to_text(content)

    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key or api_key == 'your-gemini-api-key':
        logger.warning("GEMINI_API_KEY not configured or using default placeholder. Falling back to rule-based classification.")
        return get_fallback_ai_response(agency_name, url, content)

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    prompt = (
        "You are a Nigerian government recruitment verification specialist.\n"
        "Analyze the following recruitment text and metadata.\n"
        "Return ONLY valid JSON. No markdown backticks, no explaining.\n"
        "Expected JSON Format:\n"
        "{\n"
        '  "classification": "REAL|FAKE|UNCERTAIN",\n'
        '  "confidence": 85,\n'
        '  "event_type": "RECRUITMENT_OPEN|PORTAL_CLOSED|SHORTLIST|IRRELEVANT_CHANGE",\n'
        '  "red_flags": [],\n'
        '  "extracted": {\n'
        '    "positions": "...",\n'
        '    "deadline": "...",\n'
        '    "requirements": "..."\n'
        "  }\n"
        "}\n\n"
        f"Agency: {agency_name}\n"
        f"Claimed URL: {url}\n"
        f"Content excerpt:\n{content[:2000]}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        response = requests.post(endpoint, json=payload, timeout=20)
        if response.status_code == 200:
            res_data = response.json()
            text_resp = res_data['candidates'][0]['content']['parts'][0]['text']
            # Clean markdown formatting if any
            text_resp = text_resp.replace("```json", "").replace("```", "").strip()
            return json.loads(text_resp)
        else:
            logger.error(f"Gemini API returned error {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Error calling Gemini AI: {e}")

    return get_fallback_ai_response(agency_name, url, content)


def get_fallback_ai_response(agency_name: str, url: str, content: str) -> dict:
    """Fallback classifier if Gemini is down or key is missing."""
    from apps.monitor.parser import match_recruitment_keywords, clean_html_to_text
    if '<' in content and '>' in content:
        content = clean_html_to_text(content)
    res = match_recruitment_keywords(content)

    classification = 'UNCERTAIN'
    if res['is_recruitment']:
        classification = 'REAL'

    return {
        'classification': classification,
        'confidence': 70 if res['is_recruitment'] else 30,
        'event_type': 'RECRUITMENT_OPEN' if res['is_recruitment'] else 'IRRELEVANT_CHANGE',
        'red_flags': [],
        'extracted': {
            'positions': res['positions'],
            'deadline': res['deadline'],
            'requirements': 'Check website'
        }
    }
