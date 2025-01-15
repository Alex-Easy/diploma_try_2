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
    assert product.quantity == 7  # Quantity should be updated


# Test order creation without contact
@pytest.mark.django_db
def test_create_order_without_contact(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    api_client.force_authenticate(user=user)

    data = {}
    response = api_client.post(reverse('order'), data, format='json')

    assert response.status_code == 400
    assert "contact" in response.data


# Test order creation with insufficient stock
@pytest.mark.django_db
def test_create_order_insufficient_stock(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    api_client.force_authenticate(user=user)

    contact = Contact.objects.create(user=user, city="City", street="Street", house="1", phone="1234567890")
    shop = Shop.objects.create(name="Shop 1", state=True)
    category = Category.objects.create(id=1, name="Category 1")
    product = Product.objects.create(id=1, shop=shop, category=category, name="Product 1", price=100, price_rrc=120,
                                     quantity=2)

    Basket.objects.create(user=user, product=product, quantity=5)

    data = {"contact": contact.id}
    response = api_client.post(reverse('order'), data, format='json')

    assert response.status_code == 400
    assert "Not enough stock" in response.data['error']


# Test getting a list of orders
@pytest.mark.django_db
def test_get_orders_list(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    api_client.force_authenticate(user=user)

    contact = Contact.objects.create(user=user, city="City", street="Street", house="1", phone="1234567890")
    Order.objects.create(user=user, contact=contact, status="created")
    Order.objects.create(user=user, contact=contact, status="delivered")

    response = api_client.get(reverse('order'))

    assert response.status_code == 200
    assert len(response.data['results']) == 2
    order_statuses = [order['status'] for order in response.data['results']]
    assert "created" in order_statuses
    assert "delivered" in order_statuses


# Test getting a list of orders of another user
@pytest.mark.django_db
def test_get_orders_of_other_user(api_client):
    user1 = User.objects.create_user(email="user1@example.com", password="password123")
    user2 = User.objects.create_user(email="user2@example.com", password="password123")
    api_client.force_authenticate(user=user1)

    contact = Contact.objects.create(user=user2, city="City", street="Street", house="1", phone="1234567890")
    Order.objects.create(user=user2, contact=contact, status="created")

    response = api_client.get(reverse('order'))

    assert response.status_code == 200
    # Проверяем, что раздел results пуст
    assert len(response.data['results']) == 0

