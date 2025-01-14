import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from procurement.models import Shop, Category, Product, User


@pytest.fixture
def api_client():
    return APIClient()


# Test successful upload of pricelist
@pytest.mark.django_db
def test_upload_pricelist_success(api_client):
    # Создаем пользователя и аутентифицируем его
    user = User.objects.create_user(email="supplier@example.com", password="password123")
    api_client.force_authenticate(user=user)

    # Создаем магазин и категорию
    shop = Shop.objects.create(name="Supplier Shop", state=True)
    category = Category.objects.create(id=1, name="Category 1")

    # YAML-прайс-лист
    pricelist_content = """
    - id: 1
      name: Product 1
      category: 1
      price: 100.00
      price_rrc: 120.00
      quantity: 10
      parameters: {"color": "red", "size": "L"}
    - id: 2
      name: Product 2
      category: 1
      price: 200.00
      price_rrc: 220.00
      quantity: 5
      parameters: {"color": "blue", "size": "M"}
    """
    with open("pricelist.yaml", "w") as file:
        file.write(pricelist_content)

    with open("pricelist.yaml", "rb") as file:
        response = api_client.post(reverse('upload-pricelist', args=[shop.id]), {'file': file}, format='multipart')

    # Проверяем успешное создание
    assert response.status_code == 200
    assert Product.objects.filter(name="Product 1").exists()
    assert Product.objects.filter(name="Product 2").exists()


@pytest.mark.django_db
def test_upload_pricelist_nonexistent_category(api_client):
    # Создаем пользователя и аутентифицируем его
    user = User.objects.create_user(email="supplier@example.com", password="password123")
    api_client.force_authenticate(user=user)

    # Создаем магазин
    shop = Shop.objects.create(name="Supplier Shop", state=True)

    # Прайс-лист с несуществующей категорией
    pricelist_content = """
    - id: 1
      name: Product 1
      category: 999
      price: 100.00
      price_rrc: 120.00
      quantity: 10
      parameters: {"color": "red", "size": "L"}
    """
    with open("pricelist.yaml", "w") as file:
        file.write(pricelist_content)

    with open("pricelist.yaml", "rb") as file:
        response = api_client.post(reverse('upload-pricelist', args=[shop.id]), {'file': file}, format='multipart')

    # Проверяем ошибку
    assert response.status_code == 404
    assert "Category with id 999 not found" in response.data["error"]


@pytest.mark.django_db
def test_upload_pricelist_update_existing_product(api_client):
    # Создаем пользователя и аутентифицируем его
    user = User.objects.create_user(email="supplier@example.com", password="password123")
    api_client.force_authenticate(user=user)

    # Создаем магазин, категорию и товар
    shop = Shop.objects.create(name="Supplier Shop", state=True)
    category = Category.objects.create(id=1, name="Category 1")
    product = Product.objects.create(
        id=1, name="Product 1", category=category, shop=shop,
        price=100.00, price_rrc=120.00, quantity=10, parameters={"color": "red"}
    )

    # Обновленный YAML-прайс-лист
    pricelist_content = """
    - id: 1
      name: Product 1
      category: 1
      price: 150.00
      price_rrc: 180.00
      quantity: 15
      parameters: {"color": "green"}
    """
    with open("pricelist.yaml", "w") as file:
        file.write(pricelist_content)

    with open("pricelist.yaml", "rb") as file:
        response = api_client.post(reverse('upload-pricelist', args=[shop.id]), {'file': file}, format='multipart')

    # Проверяем обновление товара
    assert response.status_code == 200
    product.refresh_from_db()
    assert product.price == 150.00
    assert product.quantity == 15
    assert product.parameters["color"] == "green"
