import pytest
from core.utils import (
    compute_content_hash,
    extract_root_domain,
    is_https,
    sanitise_html,
    truncate_text,
    format_date_nigerian,
    chunk_list,
    build_trust_badge,
)
from datetime import datetime


def test_compute_content_hash():
    content = "  Hello World   "
    hashed = compute_content_hash(content)
    assert len(hashed) == 32
    assert hashed == compute_content_hash("hello world")


def test_extract_root_domain():
    assert extract_root_domain("https://recruitment.customs.gov.ng/apply") == "customs.gov.ng"
    assert extract_root_domain("https://nnpcgroup.com/careers/") == "nnpcgroup.com"
    assert extract_root_domain("https://customs.gov.ng.application.com/") == "application.com"
    assert extract_root_domain("invalid-url") is None


def test_is_https():
    assert is_https("https://nnpcgroup.com") is True
    assert is_https("http://nnpcgroup.com") is False
    assert is_https("ftp://nnpcgroup.com") is False


def test_sanitise_html():
    html = "<div>Hello <p>World</p>!</div>"
    assert sanitise_html(html) == "Hello World !"


def test_truncate_text():
    text = "Hello World!"
    assert truncate_text(text, 100) == "Hello World!"
    assert truncate_text(text, 8) == "Hello..."


def test_format_date_nigerian():
    dt = datetime(2025, 2, 28, 10, 0, 0)
    assert format_date_nigerian(dt) in ("28 February 2025", "28 February 2025")
    assert format_date_nigerian(None) == "N/A"


def test_chunk_list():
    lst = [1, 2, 3, 4, 5]
    assert chunk_list(lst, 2) == [[1, 2], [3, 4], [5]]


def test_build_trust_badge():
    assert build_trust_badge(95) == '✅ VERIFIED OFFICIAL'
    assert build_trust_badge(75) == '✅ LIKELY OFFICIAL'
    assert build_trust_badge(55) == '⚠️ UNCONFIRMED'
    assert build_trust_badge(35) == '🔴 SUSPICIOUS'
    assert build_trust_badge(15) == '❌ FLAGGED AS FAKE'
