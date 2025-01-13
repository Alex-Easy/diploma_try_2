import pytest
from django.urls import reverse
from procurement.models import User, Shop, Category, Product, Basket, Contact, Order
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


# Test successful order creation
@pytest.mark.django_db
def test_create_order_success(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    api_client.force_authenticate(user=user)

    contact = Contact.objects.create(user=user, city="City", street="Street", house="1", phone="1234567890")
    shop = Shop.objects.create(name="Shop 1", state=True)
    category = Category.objects.create(id=1, name="Category 1")
    product = Product.objects.create(id=1, shop=shop, category=category, name="Product 1", price=100, price_rrc=120,
                                     quantity=10)

    Basket.objects.create(user=user, product=product, quantity=3)

    data = {"contact": contact.id}
    response = api_client.post(reverse('order'), data, format='json')

    print("Response status code:", response.status_code)
    print("Response data:", response.data)

    assert response.status_code == 201
    assert Order.objects.filter(user=user).exists()
    product.refresh_from_db()
    assert product.quantity == 7  # Количество уменьшилось на 3
