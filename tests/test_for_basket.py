import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from procurement.models import User, Shop, Category, Product, Basket


@pytest.fixture
def api_client():
    return APIClient()


# Test for adding product to the basket
@pytest.mark.django_db
def test_add_to_basket_success(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    api_client.force_authenticate(user=user)

    shop = Shop.objects.create(name="Test Shop", state=True)
    category = Category.objects.create(id=1, name="Category 1")
    product = Product.objects.create(
        id=1,
        shop=shop,
        category=category,
        name="Test Product",
        price=100,
        price_rrc=120,
        quantity=10,
        parameters={}
    )

    data = {
        "product": product.id,
        "quantity": 2
    }

    response = api_client.post(reverse('basket'), data, format='json')

    assert response.status_code == 201
    assert Basket.objects.filter(user=user, product=product).exists()
    basket_item = Basket.objects.get(user=user, product=product)
    assert basket_item.quantity == 2


# Test for adding insufficient stock
@pytest.mark.django_db
def test_add_to_basket_insufficient_stock(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    api_client.force_authenticate(user=user)

    shop = Shop.objects.create(name="Shop 1", state=True)
    category = Category.objects.create(id=1, name="Category 1")
    product = Product.objects.create(
        id=1, shop=shop, category=category, name="Product 1", price=100, price_rrc=120, quantity=5
    )

    data = {"product": product.id, "quantity": 10}

    response = api_client.post(reverse('basket'), data, format='json')

    # Вывод для отладки
    print("Response data:", response.data)

    assert response.status_code == 400
    assert f"Not enough stock for product {product.id}" in response.data['error']


# Test for updating basket quantity
@pytest.mark.django_db
def test_update_basket_quantity_success(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    api_client.force_authenticate(user=user)

    shop = Shop.objects.create(name="Shop 1", state=True)
    category = Category.objects.create(id=1, name="Category 1")
    product = Product.objects.create(id=1, shop=shop, category=category, name="Product 1", price=100, price_rrc=120,
                                     quantity=10)

    basket_item = Basket.objects.create(user=user, product=product, quantity=3)

    data = {"items": [{"id": basket_item.id, "quantity": 5}]}

    response = api_client.put(reverse('basket'), data, format='json')

    print("Response data:", response.data)

    assert response.status_code == 200

    basket_item.refresh_from_db()
    assert basket_item.quantity == 5


# Test for updating quantity that exceeds stock
@pytest.mark.django_db
def test_update_basket_quantity_exceed_stock(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    api_client.force_authenticate(user=user)

    shop = Shop.objects.create(name="Shop 1", state=True)
    category = Category.objects.create(id=1, name="Category 1")
    product = Product.objects.create(id=1, shop=shop, category=category, name="Product 1", price=100, price_rrc=120,
                                      quantity=5)

    basket_item = Basket.objects.create(user=user, product=product, quantity=3)

    data = {"items": [{"id": basket_item.id, "quantity": 10}]}

    response = api_client.put(reverse('basket'), data, format='json')

    print("Response data:", response.data)

    assert response.status_code == 400

    assert "Not enough stock" in response.data['error']


# Test getting basket content
@pytest.mark.django_db
def test_get_basket_content(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    api_client.force_authenticate(user=user)

    shop = Shop.objects.create(name="Shop 1", state=True)
    category = Category.objects.create(id=1, name="Category 1")
    product = Product.objects.create(
        id=1, shop=shop, category=category, name="Product 1", price=100, price_rrc=120, quantity=10
    )

    Basket.objects.create(user=user, product=product, quantity=3)

    response = api_client.get(reverse('basket'))

    print("Response status:", response.status_code)
    print("Response data:", response.data)

    assert response.status_code == 200
    assert len(response.data) == 1  # В корзине только один продукт
    assert response.data[0]['product']['name'] == "Product 1"
    assert response.data[0]['quantity'] == 3


# Test deleting basket item
@pytest.mark.django_db
def test_delete_basket_item_success(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    api_client.force_authenticate(user=user)

    shop = Shop.objects.create(name="Shop 1", state=True)
    category = Category.objects.create(id=1, name="Category 1")
    product = Product.objects.create(
        id=1, shop=shop, category=category, name="Product 1", price=100, price_rrc=120, quantity=10
    )

    basket_item = Basket.objects.create(user=user, product=product, quantity=3)

    response = api_client.delete(reverse('basket'), data={"items": [basket_item.id]}, format='json')

    print("Response status:", response.status_code)
    print("Response data:", response.data)

    assert response.status_code == 200
    assert not Basket.objects.filter(id=basket_item.id).exists()  # Убедимся, что элемент удален


# Test deleting non-existent basket item
@pytest.mark.django_db
def test_delete_nonexistent_basket_item(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    api_client.force_authenticate(user=user)

    response = api_client.delete(reverse('basket'), data={"items": [999]}, format='json')

    print("Response status:", response.status_code)
    print("Response data:", response.data)

    assert response.status_code == 400
    assert "Basket items not found" in response.data['error']

