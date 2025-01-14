import pytest
from django.urls import reverse, resolve


@pytest.mark.django_db
def test_admin_url(client):
    response = client.get('/admin/')
    assert response.status_code in [200, 302]  # 302, если требуется авторизация
    match = resolve('/admin/')
    assert match.func is not None
    assert match.view_name == 'admin:index'


@pytest.mark.django_db
def test_api_root_url(client):
    response = client.get('/api/v1/')
    assert response.status_code in [200, 401, 404]  # Проверяем доступность корневого API


@pytest.mark.django_db
def test_schema_url(client):
    response = client.get('/api/schema/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_swagger_ui_url(client):
    response = client.get('/api/docs/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_redoc_url(client):
    response = client.get('/api/redoc/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_static_files_urls(settings, client):
    settings.DEBUG = True
    response_static = client.get('/static/some-file.css')
    response_media = client.get('/media/some-image.jpg')
    assert response_static.status_code in [200, 404]
    assert response_media.status_code in [200, 404]


@pytest.mark.django_db
def test_debug_toolbar_url(settings, client):
    settings.DEBUG = True
    response = client.get('/__debug__/')
    assert response.status_code in [200, 404]