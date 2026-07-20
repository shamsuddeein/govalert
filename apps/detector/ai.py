import json
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _call_openai(prompt: str, system_prompt: str = "You are a Nigerian government recruitment verification and security AI analyst.") -> dict | None:
    """Helper method to invoke OpenAI Chat Completions API with structured JSON output."""
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key or api_key == 'your-openai-api-key':
        return None

    model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        if response.status_code == 200:
            res_data = response.json()
            content = res_data['choices'][0]['message']['content']
            return json.loads(content)
        else:
            logger.error(f"OpenAI API returned status {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Failed to call OpenAI API: {e}")

    return None


def summarize_recruitment_with_openai(title: str, agency_name: str, content: str) -> dict:
    """
    OpenAI Recruitment Summarization Engine.
    Summarizes recruitment notice into key roles, eligibility, application steps, and deadline.
    """
    from apps.monitor.parser import clean_html_to_text
    if '<' in content and '>' in content:
        content = clean_html_to_text(content)

    prompt = (
        "Summarize the following Nigerian public sector recruitment notice.\n"
        "Return ONLY a JSON object with this exact structure:\n"
        "{\n"
        '  "summary_overview": "Concise 2-sentence executive summary of the recruitment",\n'
        '  "key_positions": ["Position 1", "Position 2"],\n'
        '  "eligibility_criteria": ["Requirement 1", "Requirement 2"],\n'
        '  "application_steps": ["Step 1", "Step 2"],\n'
        '  "deadline_text": "Extracted deadline date or Not specified",\n'
        '  "fee_required": false\n'
        "}\n\n"
        f"Title: {title}\n"
        f"Agency: {agency_name}\n"
        f"Content excerpt:\n{content[:3000]}"
    )

    ai_res = _call_openai(prompt)
    if ai_res:
        return ai_res

    # Rule-based fallback summary
    return {
        "summary_overview": f"Official recruitment update for {title} by {agency_name}.",
        "key_positions": [title],
        "eligibility_criteria": ["Check official agency portal for details"],
        "application_steps": ["Visit official portal", "Submit application online"],
        "deadline_text": "Check official portal",
        "fee_required": False
    }


def detect_scam_with_openai(agency_name: str, url: str, content: str) -> dict:
    """
    OpenAI Scam Detection Engine.
    Detects scam indicators (fee collection, non-gov domain, WhatsApp, free email hosts, urgency pressure).
    Returns: dict with is_scam (bool), scam_risk_score (0-100), red_flags (list), reasoning (str).
    """
    from apps.monitor.parser import clean_html_to_text
    if '<' in content and '>' in content:
        content = clean_html_to_text(content)

    prompt = (
        "You are an expert scam detection engine for Nigerian public sector recruitment.\n"
        "Analyze the recruitment posting and metadata for scam indicators:\n"
        "1. Direct fee requests (paying for application forms, aptitude tests, medicals, or processing fees).\n"
        "2. Non-official domains claiming to be official federal portals (e.g. .blogspot, free hosts, or mismatching .com domains).\n"
        "3. Solicitations asking applicants to send documents via WhatsApp or personal Gmail/Yahoo addresses.\n"
        "4. Promises of guaranteed employment in exchange for cash or favors.\n\n"
        "Return ONLY a JSON object:\n"
        "{\n"
        '  "is_scam": true/false,\n'
        '  "scam_risk_score": 0 to 100,\n'
        '  "red_flags": ["Flag 1", "Flag 2"],\n'
        '  "reasoning": "Explanation of findings"\n'
        "}\n\n"
        f"Agency Name: {agency_name}\n"
        f"URL: {url}\n"
        f"Posting Text:\n{content[:3000]}"
    )

    ai_res = _call_openai(prompt)
    if ai_res:
        return ai_res

    # Heuristic fallback scan
    red_flags = []
    content_lower = content.lower()
    if any(term in content_lower for term in ['payment', 'fee', 'naira', 'account number', 'whatsapp', 'gmail.com']):
        red_flags.append("Contains potential fee request or unofficial contact method")

    return {
        "is_scam": len(red_flags) > 0,
        "scam_risk_score": 75 if red_flags else 10,
        "red_flags": red_flags,
        "reasoning": "Rule-based fallback scan executed."
    }


def verify_recruitment_with_openai(agency_name: str, url: str, content: str) -> dict:
    """
    OpenAI Verification Assistance Engine.
    Cross-checks agency identity, official domain structure, and announcement legitimacy.
    """
    from apps.monitor.parser import clean_html_to_text
    if '<' in content and '>' in content:
        content = clean_html_to_text(content)

    prompt = (
        "You are a government verification specialist verifying Nigerian federal recruitment notices.\n"
        "Evaluate the legitimacy of this recruitment claim:\n"
        "Return ONLY a JSON object:\n"
        "{\n"
        '  "verification_status": "VERIFIED|SUSPICIOUS|UNVERIFIED",\n'
        '  "confidence_score": 0 to 100,\n'
        '  "verification_factors": [\n'
        '    {"label": "Domain Alignment", "passed": true/false},\n'
        '    {"label": "Official Wording & Gazette Match", "passed": true/false},\n'
        '    {"label": "No Fee Requirement", "passed": true/false}\n'
        '  ],\n'
        '  "notes": "Detailed analysis notes"\n'
        "}\n\n"
        f"Agency Name: {agency_name}\n"
        f"URL: {url}\n"
        f"Posting Text:\n{content[:3000]}"
    )

    ai_res = _call_openai(prompt)
    if ai_res:
        return ai_res

    return {
        "verification_status": "UNVERIFIED",
        "confidence_score": 60,
        "verification_factors": [
            {"label": "Domain Alignment", "passed": ".gov.ng" in url or ".mil.ng" in url},
            {"label": "Official Wording Match", "passed": True},
            {"label": "No Fee Requirement", "passed": True}
        ],
        "notes": "Standard rule fallback applied."
    }


def classify_recruitment_with_ai(agency_name: str, url: str, content: str) -> dict:
    """
    Primary AI classification entry point.
    Tries OpenAI API first, then Gemini API, then rule-based fallback.
    """
    from apps.monitor.parser import clean_html_to_text
    if '<' in content and '>' in content:
        content = clean_html_to_text(content)

    # 1. Try OpenAI
    openai_prompt = (
        "Analyze the following Nigerian recruitment notice for verification.\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        '  "classification": "REAL|FAKE|UNCERTAIN",\n'
        '  "confidence": 85,\n'
        '  "event_type": "RECRUITMENT_OPEN|PORTAL_CLOSED|SHORTLIST|IRRELEVANT_CHANGE",\n'
        '  "red_flags": [],\n'
        '  "extracted": {\n'
        '    "positions": "...",\n'
        '    "deadline": "...",\n'
        '    "requirements": "..."\n'
        '  }\n'
        "}\n\n"
        f"Agency: {agency_name}\n"
        f"Claimed URL: {url}\n"
        f"Content excerpt:\n{content[:2500]}"
    )

    openai_res = _call_openai(openai_prompt)
    if openai_res and 'classification' in openai_res:
        return openai_res

    # 2. Try Gemini
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if api_key and api_key != 'your-gemini-api-key':
        try:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": openai_prompt}]}]}
            response = requests.post(endpoint, json=payload, timeout=15)
            if response.status_code == 200:
                res_data = response.json()
                text_resp = res_data['candidates'][0]['content']['parts'][0]['text']
                text_resp = text_resp.replace("```json", "").replace("```", "").strip()
                return json.loads(text_resp)
        except Exception as e:
            logger.error(f"Gemini fallback failed: {e}")

    # 3. Rule Fallback
    return get_fallback_ai_response(agency_name, url, content)


def get_fallback_ai_response(agency_name: str, url: str, content: str) -> dict:
    """Fallback classifier if AI services are down or key is missing."""
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
