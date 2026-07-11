import logging
from django.conf import settings
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


class BaseStorageBackend:
    """Base class for storage backends to abstract datastores."""
    def save_alert(self, alert_data: dict):
        raise NotImplementedError

    def get_alert(self, alert_id: int) -> dict:
        raise NotImplementedError

    def get_subscribers_for_agency(self, agency_id: int) -> list:
        raise NotImplementedError


class DjangoORMStorageBackend(BaseStorageBackend):
    """Django Database (SQLite/PostgreSQL) implementation of StorageBackend."""
    def save_alert(self, alert_data: dict):
        from apps.alerts.models import Alert
        return Alert.objects.create(**alert_data)

    def get_alert(self, alert_id: int) -> dict:
        from apps.alerts.models import Alert
        alert = Alert.objects.get(pk=alert_id)
        return {
            'id': alert.id,
            'agency_acronym': alert.agency.acronym,
            'title': alert.title,
            'positions': alert.positions,
            'deadline': alert.deadline,
            'requirements': alert.requirements,
            'source_url': alert.source_url,
            'trust_score': alert.trust_score,
            'ai_classification': alert.ai_classification,
        }

    def get_subscribers_for_agency(self, agency_id: int) -> list:
        from apps.subscriptions.models import Subscription
        from apps.accounts.models import UserState
        subscriptions = Subscription.objects.filter(
            agency_id=agency_id,
            is_active=True,
            user__state=UserState.ACTIVE
        ).select_related('user')
        return [sub.user for sub in subscriptions]


_backend_cache = None

def get_storage_backend() -> BaseStorageBackend:
    """Load and return the configured storage backend."""
    global _backend_cache
    if _backend_cache is None:
        backend_path = getattr(settings, 'STORAGE_BACKEND', 'core.storage.DjangoORMStorageBackend')
        try:
            backend_class = import_string(backend_path)
            _backend_cache = backend_class()
            logger.info(f"Loaded storage backend: {backend_path}")
        except Exception as e:
            logger.error(f"Failed to load storage backend {backend_path}: {e}. Defaulting to DjangoORMStorageBackend.")
            _backend_cache = DjangoORMStorageBackend()
    return _backend_cache
