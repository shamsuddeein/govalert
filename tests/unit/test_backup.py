import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from storage.backup import export_and_backup
from django.conf import settings


@pytest.mark.django_db
@patch('requests.post')
def test_export_and_backup(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        'ok': True,
        'result': {'message_id': 12345}
    }
    mock_post.return_value = mock_resp

    temp_dir = tempfile.TemporaryDirectory()
    index_path = Path(temp_dir.name) / "index.json"

    with patch.object(settings, 'INDEX_JSON_PATH', index_path), \
         patch.object(settings, 'TELEGRAM_BACKUP_CHANNEL_ID', -100123456789), \
         patch.object(settings, 'TELEGRAM_BOT_TOKEN', 'mock-token'):
        res = export_and_backup()
        assert res is True

        assert index_path.exists()
        with open(index_path) as f:
            data = json.load(f)
            assert data['backup_channel']['last_backup_id'] == 12345

    temp_dir.cleanup()
