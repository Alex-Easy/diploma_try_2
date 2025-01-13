from django.urls import reverse
from procurement.models import Shop
import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


# Test successful getting of shop list
@pytest.mark.django_db
def test_get_shop_list(api_client):
    # Создаём несколько магазинов
    Shop.objects.create(name="Shop 1", state=True)
    Shop.objects.create(name="Shop 2", state=True)
    Shop.objects.create(name="Inactive Shop", state=False)

    # Запрос на получение списка магазинов
    response = api_client.get(reverse('shop-list'))

    assert response.status_code == 200
    assert len(response.data['results']) == 2  # Проверяем только активные магазины
    shop_names = [shop['name'] for shop in response.data['results']]
    assert "Shop 1" in shop_names
    assert "Shop 2" in shop_names
    assert "Inactive Shop" not in shop_names
