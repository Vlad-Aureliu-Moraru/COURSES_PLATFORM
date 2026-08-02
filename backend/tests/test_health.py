from rest_framework.test import APIClient


def test_health_check_ok(db):
    client = APIClient()
    response = client.get('/api/v1/health/')

    assert response.status_code == 200
    assert response.data['status'] == 'ok'
    assert response.data['database'] == 'ok'
    assert 'last_migration' in response.data
    assert 'disk_usage_percent' in response.data
