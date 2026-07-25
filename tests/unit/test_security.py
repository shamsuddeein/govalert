import pytest
from core.security import validate_outbound_url
from core.exceptions import ScraperException


def test_ssrf_rejects_loopback():
    with pytest.raises(ScraperException, match="private IP"):
        validate_outbound_url("http://127.0.0.1/admin")


def test_ssrf_rejects_aws_metadata():
    with pytest.raises(ScraperException, match="private IP"):
        validate_outbound_url("http://169.254.169.254/latest/meta-data/")


def test_ssrf_rejects_private_10_network():
    with pytest.raises(ScraperException, match="private IP"):
        validate_outbound_url("http://10.0.0.1/internal")


def test_ssrf_rejects_private_192_network():
    with pytest.raises(ScraperException, match="private IP"):
        validate_outbound_url("http://192.168.1.1/")


def test_ssrf_rejects_non_http_scheme():
    with pytest.raises(ScraperException, match="non-HTTP scheme"):
        validate_outbound_url("file:///etc/passwd")


def test_ssrf_allows_valid_public_domain():
    # Should not raise any exception for legitimate public URL
    validate_outbound_url("https://www.google.com")
