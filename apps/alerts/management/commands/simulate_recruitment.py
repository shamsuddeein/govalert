# Test with a real portal URL (you provide the URL)?
from django.core.management.base import BaseCommand
from django.conf import settings

import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Simulate a recruitment detection run for Test 1. By default will not send Telegram messages."

    def add_arguments(self, parser):
        parser.add_argument('--dispatch', action='store_true', help='Allow dispatch to subscribers (may send Telegram messages)')
        parser.add_argument('--post-events', action='store_true', help='Post JSON event to events/public channels')

    def handle(self, *args, **options):
        from apps.agencies.models import Agency, Portal
        from apps.alerts.services import create_alert_from_scrape
        from apps.alerts.models import RecruitmentEvent, DecisionLog, Alert

        dispatch_allowed = options.get('dispatch', False)
        post_events = options.get('post_events', False)

        # Create or get test agency + portal
        agency, _ = Agency.objects.get_or_create(
            acronym='SIM',
            defaults={'name': 'Simulation Agency', 'official_domains': ['example.gov']}
        )

        portal, _ = Portal.objects.get_or_create(
            agency=agency,
            name='Simulation Portal',
            defaults={'url': 'https://example.gov/sim-recruitment', 'scrape_method': 'HTTP'}
        )

        # Sample scraped content
        content = (
            "<html><body>SIM Recruitment 2026 is now open. "
            "Visit https://example.gov/sim-recruitment to apply. Deadline: 2026-09-30. "
            "Positions: Officer, Clerk. No fees required.</body></html>"
        )

        matched_data = {
            'positions': 'Officer, Clerk',
            'deadline': '2026-09-30',
            'rule_matches': ['recruitment_keyword', 'apply_keyword']
        }

        # If dispatch is not allowed, stub out the notification sender to avoid real Telegram sends
        if not dispatch_allowed:
            try:
                import apps.notifications.tasks as notif_tasks

                def _fake_send(*args, **kwargs):
                    logger.info('Simulated send_message called (dispatch suppressed).')
                    return {'message_id': 999999}

                notif_tasks.send_message = _fake_send
            except Exception:
                # If tasks imported differently, ignore — dispatch will be skipped if no subscribers
                pass

        self.stdout.write('Running simulated detection...')

        alert = create_alert_from_scrape(portal, content, matched_data)

        if not alert:
            self.stdout.write(self.style.ERROR('No alert created.'))
            return

        # Show results
        self.stdout.write(self.style.SUCCESS(f'Created RecruitmentEvent: {alert.recruitment_event.event_id}'))
        self.stdout.write(f'Alert ID: {alert.id} status={alert.status} trust={alert.trust_score}')

        # DecisionLog
        try:
            dl = DecisionLog.objects.get(event=alert.recruitment_event)
            self.stdout.write(f'DecisionLog: trust={dl.final_trust} gemini={dl.gemini_score} rules={dl.rule_matches}')
        except DecisionLog.DoesNotExist:
            self.stdout.write('DecisionLog not found.')

        # Optionally post event JSON to events/public channels
        if post_events:
            try:
                from storage.events import write_event, post_public_alert

                ev = alert.recruitment_event
                agency_name = agency.name
                acronym = agency.acronym
                category = agency.category
                title = alert.title
                url = portal.url
                trust = alert.trust_score
                deadline = alert.deadline
                positions = alert.positions
                content_hash = ev.content_hash

                written = write_event(ev.event_id, ev.event_type, agency_name, acronym, category, title, url, trust, deadline, positions, status='verified', content_hash=content_hash)
                self.stdout.write(f'Events channel write: {written}')

                public_id = post_public_alert(f"{title}\n{url}\nTrust: {trust}")
                self.stdout.write(f'Public channel post id: {public_id}')
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f'Could not post events: {exc}'))

        self.stdout.write(self.style.SUCCESS('Simulation complete.'))
