import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.agencies.models import Agency
from apps.alerts.models import Alert, AlertStatus, EventType


@pytest.mark.django_db
def test_agency_list_api():
    client = APIClient()
    Agency.objects.create(
        name="Nigeria Customs Service",
        acronym="NCS",
        official_domains=["customs.gov.ng"],
        is_active=True
    )
    url = reverse('api:agency_list')
    response = client.get(url)
    assert response.status_code == 200
    results = response.data.get('results', response.data)  # handle paginated or plain list
    assert len(results) == 1
    assert results[0]['acronym'] == 'NCS'


@pytest.mark.django_db
def test_job_list_api():
    client = APIClient()
    agency = Agency.objects.create(
        name="Nigeria Customs Service",
        acronym="NCS",
        official_domains=["customs.gov.ng"],
        is_active=True
    )
    Alert.objects.create(
        agency=agency,
        title="Customs Recruitment 2025",
        status=AlertStatus.APPROVED,
        event_type=EventType.RECRUITMENT_OPEN
    )
    url = reverse('api:job_list')
    response = client.get(url)
    assert response.status_code == 200
    results = response.data.get('results', response.data)
    assert len(results) == 1
    assert results[0]['title'] == 'Customs Recruitment 2025'


@pytest.mark.django_db
def test_pending_alerts_excluded_from_public_api():
    """
    REGRESSION TEST for the PENDING alert exposure bug.
    Unapproved (PENDING) alerts must NEVER appear in the public /api/v1/jobs/ list
    or be accessible via /api/v1/jobs/{ref}/.
    """
    client = APIClient()
    agency = Agency.objects.create(
        name="Nigeria Customs Service",
        acronym="NCS",
        official_domains=["customs.gov.ng"],
        is_active=True
    )
    approved = Alert.objects.create(
        agency=agency,
        title="Approved Recruitment 2025",
        status=AlertStatus.APPROVED,
        event_type=EventType.RECRUITMENT_OPEN
    )
    pending = Alert.objects.create(
        agency=agency,
        title="Pending (Unreviewed) Alert",
        status=AlertStatus.PENDING,
        event_type=EventType.RECRUITMENT_OPEN
    )

    # List endpoint must return exactly 1 result (the approved one)
    list_url = reverse('api:job_list')
    response = client.get(list_url)
    assert response.status_code == 200
    results = response.data.get('results', response.data)
    assert len(results) == 1, (
        f"Expected 1 result, got {len(results)}: "
        "PENDING alert is leaking into the public job list"
    )
    assert results[0]['title'] == 'Approved Recruitment 2025'

    # Detail endpoint for PENDING alert must return 404, not the alert data
    pending_ref = f"{pending.pk:04d}-GA"
    detail_url = reverse('api:job_detail', kwargs={'ref': pending_ref})
    detail_response = client.get(detail_url)
    assert detail_response.status_code == 404, (
        "PENDING alert is accessible via the detail endpoint — must return 404"
    )


from unittest.mock import patch
from django.contrib.auth.models import User

@pytest.mark.django_db
@patch('apps.notifications.sender.send_message')
def test_admin_broadcast_api(mock_send):
    client = APIClient()
    user = User.objects.create_superuser(username='superadmin', password='password', email='admin@example.com')
    client.force_authenticate(user=user)

    from apps.accounts.models import TelegramUser
    TelegramUser.objects.create(telegram_id=123, first_name="Test", state="ACTIVE")

    url = reverse('api:admin_broadcast')
    response = client.post(url, {'text': 'Hello All!'}, format='json')
    assert response.status_code == 200
    assert response.data['status'] == 'broadcast_sent'
    assert response.data['recipients_count'] == 1
    mock_send.assert_called_once_with(chat_id=123, text='Hello All!')


@pytest.mark.django_db
def test_health_api():
    client = APIClient()
    url = reverse('api:health')
    response = client.get(url)
    assert response.status_code == 200
    assert response.data['status'] in ['ok', 'degraded']
    assert 'database' in response.data
    assert 'telegram' in response.data
    assert 'scheduler' in response.data
    assert 'active_scrapers' in response.data  # key is 'active_scrapers', not 'scrapers'


@pytest.mark.django_db
def test_token_obtain_email_api():
    from django.contrib.auth.models import User
    User.objects.create_superuser(username='testadmin', password='testpassword', email='admin@govalert.ng')
    
    client = APIClient()
    url = reverse('api:token_obtain')
    
    # Try using email and password
    response = client.post(url, {'email': 'admin@govalert.ng', 'password': 'testpassword'}, format='json')
    assert response.status_code == 200
    assert 'access' in response.data
    assert 'refresh' in response.data

    # Try using username in the email field (fallback)
    response_fb = client.post(url, {'email': 'testadmin', 'password': 'testpassword'}, format='json')
    assert response_fb.status_code == 200
    assert 'access' in response_fb.data


@pytest.mark.django_db
def test_email_backend_and_form():
    from django.contrib.auth.models import User
    from apps.accounts.forms import EmailAdminAuthenticationForm
    from django.contrib.auth import authenticate
    
    # Create admin user
    user = User.objects.create_superuser(username='formadmin', password='formpassword', email='form@govalert.ng')
    
    # Test EmailAdminAuthenticationForm with email
    form = EmailAdminAuthenticationForm(None, data={'username': 'form@govalert.ng', 'password': 'formpassword'})
    assert form.is_valid()
    assert form.user_cache == user
    
    # Test EmailAdminAuthenticationForm with username fallback
    form_fb = EmailAdminAuthenticationForm(None, data={'username': 'formadmin', 'password': 'formpassword'})
    assert form_fb.is_valid()
    assert form_fb.user_cache == user

    # Test direct authentication with email
    authenticated_user = authenticate(username='form@govalert.ng', password='formpassword')
    assert authenticated_user == user


@pytest.mark.django_db
def test_admin_system_health_api():
    from django.contrib.auth.models import User
    from apps.agencies.models import Agency, Portal
    from apps.monitor.models import Snapshot

    staff_user = User.objects.create_user(username='staffuser', password='password', is_staff=True)
    client = APIClient()
    client.force_authenticate(user=staff_user)

    agency = Agency.objects.create(name="Customs", acronym="NCS", category="FINANCE", official_domains=["customs.gov.ng"], is_active=True)
    portal = Portal.objects.create(agency=agency, name="Customs Portal", url="https://customs.gov.ng", health_status="OFFLINE", consecutive_failures=3, is_active=True)
    Snapshot.objects.create(portal=portal, status_code=500, response_time_ms=300)

    url = reverse('api:admin_system_health')
    response = client.get(url)
    assert response.status_code == 200
    assert 'system_status' in response.data
    assert 'portals_breakdown' in response.data
    assert 'recent_failed_snapshots' in response.data
    assert 'daily_trend_7_days' in response.data
    assert len(response.data['portals_breakdown']) >= 1
    assert len(response.data['recent_failed_snapshots']) >= 1


@pytest.mark.django_db
def test_management_commands_audit_and_reconcile():
    from django.core.management import call_command
    from apps.agencies.models import Agency, Portal

    agency = Agency.objects.create(name="Army", acronym="Army", category="SECURITY", official_domains=["army.mil.ng"], is_active=True)
    # Create duplicate portals to simulate duplicate database records
    Portal.objects.create(agency=agency, name="Army 1", url="https://nda.edu.ng")
    Portal.objects.create(agency=agency, name="Army 2", url="https://nda.edu.ng")

    call_command('audit_agency_data')
    call_command('reconcile_agency_data')
    call_command('load_ng_portals')

    # Verify duplicate portal was safely cleaned up
    assert Portal.objects.filter(url="https://nda.edu.ng").count() == 1


@pytest.mark.django_db
def test_keyword_subscription_api():
    from django.core.cache import cache
    from apps.subscriptions.models import KeywordSubscription

    cache.clear()
    client = APIClient()
    url = reverse('api:keyword_subscriptions')

    # Test invalid email
    res = client.post(url, {'email': 'invalid-email', 'query_text': 'NNPC'}, format='json')
    assert res.status_code == 400

    # Test missing query
    res = client.post(url, {'email': 'test@example.com', 'query_text': ''}, format='json')
    assert res.status_code == 400

    # Test valid submission
    res = client.post(url, {'email': 'test@example.com', 'query_text': 'NNPC'}, format='json')
    assert res.status_code == 201
    assert "test@example.com" in res.data['detail']
    assert KeywordSubscription.objects.filter(email='test@example.com', query_text='NNPC').exists()


@pytest.mark.django_db
def test_keyword_subscription_matching():
    from apps.subscriptions.models import KeywordSubscription
    from apps.subscriptions.services import match_keyword_subscriptions_for_alert
    from apps.agencies.models import Agency
    from apps.alerts.models import Alert, AlertStatus, EventType

    KeywordSubscription.objects.create(email='subscriber@example.com', query_text='Customs', is_active=True)
    agency = Agency.objects.create(name="Nigeria Customs Service", acronym="NCS", official_domains=["customs.gov.ng"], is_active=True)
    alert = Alert.objects.create(
        agency=agency,
        title="Customs Officer Cadet Recruitment",
        status=AlertStatus.APPROVED,
        event_type=EventType.RECRUITMENT_OPEN
    )

    matches = match_keyword_subscriptions_for_alert(alert)
    assert matches == 1

    sub = KeywordSubscription.objects.get(email='subscriber@example.com')
    assert sub.last_matched_at is not None


@pytest.mark.django_db
def test_admin_agency_search_api():
    """
    REGRESSION TEST for BUG 1: Agency search 500s due to NameError 'models' not defined.
    Verifies /api/v1/admin/agencies/?search=army returns 200 with filtered results.
    """
    from django.contrib.auth.models import User
    from apps.agencies.models import Agency

    staff_user = User.objects.create_user(
        username="admin_user",
        email="admin@example.com",
        password="Password123!",
        is_staff=True
    )
    Agency.objects.create(name="Nigerian Army", acronym="NA", official_domains=["army.mil.ng"], is_active=True)
    Agency.objects.create(name="Nigeria Police Force", acronym="NPF", official_domains=["police.gov.ng"], is_active=True)

    client = APIClient()
    client.force_authenticate(user=staff_user)

    url = reverse('api:admin_agency_list_create') + '?search=army'
    response = client.get(url)
    assert response.status_code == 200
    results = response.data
    assert len(results) == 1
    assert results[0]['acronym'] == 'NA'


@pytest.mark.django_db
def test_clean_html_to_text_nul_bytes_and_non_html():
    """
    REGRESSION TEST for BUG 2: clean_html_to_text handling of NUL bytes and non-HTML content.
    """
    from apps.monitor.parser import clean_html_to_text

    # NUL bytes stripped
    raw = "Hello\x00 World\x00 <script>alert(1)</script> <b>Test</b>"
    cleaned = clean_html_to_text(raw, content_type="text/html")
    assert "\x00" not in cleaned
    assert "Hello World" in cleaned

    # Non-HTML content type skipped
    non_html = "Binary/PDF content \x00 data..."
    cleaned_non_html = clean_html_to_text(non_html, content_type="application/pdf")
    assert "\x00" not in cleaned_non_html
    assert "Binary/PDF content" in cleaned_non_html


@pytest.mark.django_db
def test_admin_portal_trigger_check_error_handling(mocker):
    """
    REGRESSION TEST for BUG 2: Manual portal check returning non-500 response on parse/encoding error.
    """
    from django.contrib.auth.models import User
    from apps.agencies.models import Agency, Portal

    staff_user = User.objects.create_user(
        username="admin_user_2",
        email="admin2@example.com",
        password="Password123!",
        is_staff=True
    )
    agency = Agency.objects.create(name="INEC", acronym="INEC", official_domains=["recruitment.inecnigeria.org"], is_active=True)
    portal = Portal.objects.create(agency=agency, name="INEC Portal", url="https://recruitment.inecnigeria.org")

    mocker.patch('apps.monitor.tasks.portal_check', side_effect=ValueError("A string literal cannot contain NUL (0x00) characters."))

    client = APIClient()
    client.force_authenticate(user=staff_user)

    url = reverse('api:admin_portal_trigger_check', kwargs={'pk': portal.id})
    response = client.post(url)
    assert response.status_code == 422
    assert "could not be parsed" in response.data['detail']


@pytest.mark.django_db
def test_job_list_deduplication_by_fingerprint_and_title():
    """
    REGRESSION TEST: Ensure JobListView deduplicates alerts sharing the same agency and title
    or fingerprint, returning only the single latest Alert.
    """
    client = APIClient()
    agency = Agency.objects.create(
        name="Nigerian Maritime Administration and Safety Agency",
        acronym="NIMASA",
        official_domains=["nimasa.gov.ng"],
        is_active=True
    )
    # Older alert
    alert1 = Alert.objects.create(
        agency=agency,
        title="NIMASA Recruitment Update Detected",
        status=AlertStatus.APPROVED,
        event_type=EventType.RECRUITMENT_OPEN
    )
    # Newer alert for same recruitment
    alert2 = Alert.objects.create(
        agency=agency,
        title="NIMASA Recruitment Update Detected",
        status=AlertStatus.APPROVED,
        event_type=EventType.RECRUITMENT_OPEN
    )

    url = reverse('api:job_list')
    response = client.get(url)
    assert response.status_code == 200
    results = response.data.get('results', response.data)
    assert len(results) == 1
    assert results[0]['ref'] == f"{alert2.pk:04d}-GA"


@pytest.mark.django_db
def test_supersede_older_alerts_on_update():
    """
    Ensure calling supersede_older_alerts updates older APPROVED alerts for the same fingerprint/title to SUPERSEDED.
    """
    from apps.alerts.services import supersede_older_alerts
    agency = Agency.objects.create(
        name="Federal Ministry of Interior",
        acronym="FMI",
        official_domains=["interior.gov.ng"],
        is_active=True
    )
    old_alert = Alert.objects.create(
        agency=agency,
        title="FMI Recruitment Update Detected",
        status=AlertStatus.APPROVED,
        event_type=EventType.RECRUITMENT_OPEN
    )
    new_alert = Alert.objects.create(
        agency=agency,
        title="FMI Recruitment Update Detected",
        status=AlertStatus.APPROVED,
        event_type=EventType.RECRUITMENT_OPEN
    )

    count = supersede_older_alerts(new_alert)
    assert count == 1
    old_alert.refresh_from_db()
    assert old_alert.status == AlertStatus.SUPERSEDED






