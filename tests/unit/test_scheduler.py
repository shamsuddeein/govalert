import pytest
from unittest.mock import patch, MagicMock
from config.scheduler import get_scheduler, start


def test_get_scheduler():
    scheduler = get_scheduler()
    assert scheduler is not None
    assert str(scheduler.timezone) == 'Africa/Lagos'


@patch('config.scheduler.get_scheduler')
def test_scheduler_start(mock_get):
    mock_sched = MagicMock()
    mock_sched.running = False
    mock_get.return_value = mock_sched

    with patch('django.conf.settings.PORTAL_CHECK_INTERVAL_HIGH_PRIORITY', 10), \
         patch('django.conf.settings.PORTAL_CHECK_INTERVAL_MINUTES', 15), \
         patch('django.conf.settings.PORTAL_CHECK_INTERVAL_LOW_ACTIVITY', 30):
        start()

    assert mock_sched.add_job.call_count >= 5
    mock_sched.start.assert_called_once()
