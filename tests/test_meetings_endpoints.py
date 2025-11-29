import json
import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_get_meetings(client):
    rv = client.get('/api/meetings')
    data = rv.get_json()
    assert rv.status_code == 200
    assert data.get('success') is True
    assert isinstance(data.get('meetings'), list)


def test_telegram_join_and_post_message(client):
    # Join a meeting via Telegram join endpoint
    rv = client.post('/api/meetings/1/telegram-join', json={'telegram_id': 9999, 'name': 'Test User'})
    data = rv.get_json()
    assert rv.status_code == 200
    assert data.get('success') is True
    # Post a message
    rv2 = client.post('/api/meetings/1/messages', json={'sender': 'Test User', 'text': 'Hello from test'})
    data2 = rv2.get_json()
    assert rv2.status_code == 201
    assert data2.get('success') is True
    assert 'message' in data2
