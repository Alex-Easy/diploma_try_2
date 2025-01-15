import pytest
from django.urls import reverse
from procurement.models import Category


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


# Test successful get category list
@pytest.mark.django_db
def test_get_category_list(api_client):
    Category.objects.create(id=1, name="Category 1")
    Category.objects.create(id=2, name="Category 2")

    response = api_client.get(reverse('category-list'))

    assert response.status_code == 200
    assert response.data['count'] == 2  # Проверяем общее количество категорий
    assert len(response.data['results']) == 2  # Проверяем количество объектов в results
    category_names = [category['name'] for category in response.data['results']]
    assert "Category 1" in category_names
    assert "Category 2" in category_names

