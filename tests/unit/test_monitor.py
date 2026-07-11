import pytest
from unittest.mock import patch, MagicMock
from apps.monitor.scraper import scrape_portal
from apps.monitor.parser import clean_html_to_text, analyze_diff, match_recruitment_keywords
from core.exceptions import ScraperException


def test_clean_html_to_text():
    html = "<html><head><title>Test</title></head><body><nav>Menu</nav><main><h1>Job Openings</h1><p>Apply for positions.</p></main><footer>Foot</footer></body></html>"
    text = clean_html_to_text(html)
    assert "Menu" not in text
    assert "Foot" not in text
    assert "Job Openings Apply for positions." in text


def test_analyze_diff():
    old = "Line 1\nLine 2"
    new = "Line 1\nLine 2\nLine 3"
    assert analyze_diff(old, new) == "Line 3"


def test_match_recruitment_keywords():
    text = "NCS Recruitment 2025. Apply now for multiple positions. Deadline is December 31, 2025."
    res = match_recruitment_keywords(text)
    assert res['is_recruitment'] is True
    assert res['confidence'] == 'HIGH'
    assert "December 31, 2025" in res['deadline']


@patch('apps.monitor.scraper.requests.get')
def test_scrape_portal_http_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.text = "Hello World"
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp

    content, code, duration = scrape_portal("http://example.com", method="HTTP")
    assert content == "Hello World"
    assert code == 200
    assert duration >= 0


import requests


@patch('apps.monitor.scraper.requests.get')
def test_scrape_portal_http_fail(mock_get):
    mock_get.side_effect = requests.RequestException("Connection Refused")
    with pytest.raises(ScraperException):
        scrape_portal("http://example.com", method="HTTP")
