import pytest
from apps.monitor.parser import validate_and_sanitize_deadline, match_recruitment_keywords


def test_validate_and_sanitize_deadline_invalid_pattern():
    # "31 of 1993" was extracted from stats text "31 of 1993 teachers"
    result = validate_and_sanitize_deadline("31 of 1993")
    assert result == "Not Specified"


def test_validate_and_sanitize_deadline_past_year():
    # 2024 date when current year is 2026
    result = validate_and_sanitize_deadline("30th September 2024")
    assert result == "Not Specified"


def test_validate_and_sanitize_deadline_valid_future():
    result = validate_and_sanitize_deadline("30th September 2026")
    assert result == "30th September 2026"


def test_trcn_scraped_text_extraction():
    trcn_text = """
    Federal Ministry of Education Teachers Registration Council of Nigeria Empowering Nigerian Teachers
    Register your teaching credentials, verify any educator's licence.
    Registered teachers 1.6M+ Certificates issued 1.6M+ States covered 36 + FCT Register verification 24/7.
    31 of 1993 accredited institutions.
    """
    res = match_recruitment_keywords(trcn_text)
    assert res['deadline'] == "Not Specified"


def test_fmi_scraped_text_past_date_extraction():
    fmi_text = """
    Federal Ministry of Interior Recruitment Notice.
    Application Deadline: 30th September 2024
    Requirements Extracted: Check website
    """
    res = match_recruitment_keywords(fmi_text)
    assert res['deadline'] == "Not Specified"


def test_fmi_scraped_text_valid_date_extraction():
    fmi_text = """
    Federal Ministry of Interior Recruitment Notice.
    Application Deadline: 30th September 2026
    Requirements Extracted: Check website
    """
    res = match_recruitment_keywords(fmi_text)
    assert res['deadline'] == "30th September 2026"
