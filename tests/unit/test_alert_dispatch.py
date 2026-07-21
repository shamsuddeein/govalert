import pytest
from unittest.mock import patch

from apps.accounts.models import TelegramUser, UserState
from apps.agencies.models import Agency, Portal
from apps.alerts.models import Alert, AlertStatus, EventStatus, EventType, RecruitmentEvent
from apps.notifications.tasks import dispatch_alert
from apps.subscriptions.models import Subscription, TelegramJobWatch


@pytest.mark.django_db
@patch('apps.notifications.tasks.send_message', return_value={'message_id': 1})
@patch('storage.events.post_public_alert')
@patch('apps.subscriptions.services.match_keyword_subscriptions_for_alert')
def test_update_dispatches_once_to_general_feed_and_chain_watchers(mock_keyword, mock_public, mock_send):
    agency = Agency.objects.create(name='Nigeria Customs Service', acronym='NCS', official_domains=['customs.gov.ng'])
    portal = Portal.objects.create(agency=agency, name='Careers', url='https://customs.gov.ng/careers')
    initial_event = RecruitmentEvent.objects.create(
        event_id='evt_initial', fingerprint='a' * 64, portal=portal, status=EventStatus.NEW,
        event_type=EventType.RECRUITMENT_OPEN, title='Recruitment', positions='Officer',
    )
    initial_alert = Alert.objects.create(agency=agency, portal=portal, recruitment_event=initial_event, title='Recruitment', status=AlertStatus.APPROVED)
    update_event = RecruitmentEvent.objects.create(
        event_id='evt_update', fingerprint='a' * 64, portal=portal, status=EventStatus.UPDATED,
        previous_event=initial_event, event_type=EventType.DEADLINE_EXTENDED,
        title='Recruitment deadline extended', positions='Officer',
    )
    update_alert = Alert.objects.create(agency=agency, portal=portal, recruitment_event=update_event, title='Recruitment deadline extended', status=AlertStatus.APPROVED)

    general = TelegramUser.objects.create(telegram_id=1, first_name='General', state=UserState.ACTIVE, consented_to_data_policy=True)
    opted_out = TelegramUser.objects.create(telegram_id=2, first_name='Opted out', state=UserState.ACTIVE, consented_to_data_policy=True)
    watcher = TelegramUser.objects.create(telegram_id=3, first_name='Watcher', state=UserState.ACTIVE, consented_to_data_policy=True)
    Subscription.objects.create(user=general, agency=agency, is_active=True)
    Subscription.objects.create(user=opted_out, agency=agency, is_active=False)
    TelegramJobWatch.objects.create(user=watcher, alert=initial_alert, is_active=True)

    dispatch_alert(update_alert.id)

    recipients = {call.kwargs['chat_id'] for call in mock_send.call_args_list}
    assert recipients == {general.telegram_id, watcher.telegram_id}
    assert mock_send.call_count == 2
