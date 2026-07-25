import pytest
from apps.agencies.models import Agency, Portal, HealthStatus, PortalStatus
from apps.agencies.management.commands.seed_agencies import Command as SeedCommand


@pytest.mark.django_db
def test_credicorp_portal_url_is_careers_page():
    # Seed agencies
    cmd = SeedCommand()
    cmd.handle(dry_run=False)

    agency = Agency.objects.get(acronym='CREDICORP')
    portal = Portal.objects.get(agency=agency)

    # Must be set to dedicated careers page https://credicorp.ng/careers
    assert portal.url == 'https://credicorp.ng/careers'
    assert 'clickd' not in portal.url
