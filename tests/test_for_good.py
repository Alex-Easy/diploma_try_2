import pytest
from django.urls import reverse
from procurement.models import Shop, Category, Product
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


# Test getting a list of products
@pytest.mark.django_db
def test_get_product_list(api_client):
    # Создаем магазин, категорию и товары
    shop = Shop.objects.create(name="Shop 1", state=True)
    category = Category.objects.create(id=1, name="Category 1")
    Product.objects.create(
        id=1,
        shop=shop,
        category=category,
        name="Product 1",
        price=100,
        price_rrc=120,
        quantity=10,
        parameters={"color": "red", "size": "M"}
    )
    Product.objects.create(
        id=2,
        shop=shop,
        category=category,
        name="Product 2",
        price=200,
        price_rrc=220,
        quantity=5,
        parameters={"color": "blue", "size": "L"}
    )

    # Запрос списка товаров
    response = api_client.get(reverse('product-list'))

    # Проверка успешного получения данных
    assert response.status_code == 200
    assert len(response.data['results']) == 2
    product_names = [product['name'] for product in response.data['results']]
    assert "Product 1" in product_names
    assert "Product 2" in product_names


# Test filtering products by category
@pytest.mark.django_db
def test_filter_products_by_category(api_client):
    # Создаем магазин, категории и товары
    shop = Shop.objects.create(name="Shop 1", state=True)
    category1 = Category.objects.create(id=1, name="Category 1")
    category2 = Category.objects.create(id=2, name="Category 2")
    Product.objects.create(
        id=1,
        shop=shop,
        category=category1,
        name="Product 1",
        price=100,
        price_rrc=120,
        quantity=10,
        parameters={}
    )
    Product.objects.create(
        id=2,
        shop=shop,
        category=category2,
        name="Product 2",
        price=200,
        price_rrc=220,
        quantity=5,
        parameters={}
    )

    # Фильтрация по категории 1
    response = api_client.get(reverse('product-list') + f"?category_id={category1.id}")
    assert response.status_code == 200
    assert response.data['count'] == 1  # Проверяем количество продуктов
    assert response.data['results'][0]['name'] == "Product 1"  # Проверяем первый элемент списка

    # Фильтрация по категории 2
    response = api_client.get(reverse('product-list') + f"?category_id={category2.id}")
    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['name'] == "Product 2"


# Test filtering products by shop
@pytest.mark.django_db
def test_filter_products_by_shop(api_client):
    # Создаем магазины, категорию и товары
    shop1 = Shop.objects.create(name="Shop 1", state=True)
    shop2 = Shop.objects.create(name="Shop 2", state=True)
    category = Category.objects.create(id=1, name="Category 1")
    Product.objects.create(
        id=1,
        shop=shop1,
        category=category,
        name="Product 1",
        price=100,
        price_rrc=120,
        quantity=10,
        parameters={}
    )
    Product.objects.create(
        id=2,
        shop=shop2,
        category=category,
        name="Product 2",
        price=200,
        price_rrc=220,
        quantity=5,
        parameters={}
    )

    # Фильтрация по магазину 1
    response = api_client.get(reverse('product-list') + f"?shop_id={shop1.id}")
    assert response.status_code == 200
    assert response.data['count'] == 1  # Проверяем количество продуктов
    assert response.data['results'][0]['name'] == "Product 1"  # Проверяем содержимое первого элемента

    # Фильтрация по магазину 2
    response = api_client.get(reverse('product-list') + f"?shop_id={shop2.id}")
    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['name'] == "Product 2"


# Test filtering products with invalid parameters
@pytest.mark.django_db
def test_filter_products_with_invalid_params(api_client):
    # Запрос с несуществующей категорией
    response = api_client.get(reverse('product-list') + "?category_id=999")
    assert response.status_code == 200  # Ошибки нет, просто пустой результат
    assert response.data['count'] == 0  # Убедимся, что количество равно 0
    assert response.data['results'] == []  # Убедимся, что список пуст

    # Запрос с несуществующим магазином
    response = api_client.get(reverse('product-list') + "?shop_id=999")
    assert response.status_code == 200  # Ошибки нет, просто пустой результат
    assert response.data['count'] == 0  # Убедимся, что количество равно 0
    assert response.data['results'] == []  # Убедимся, что список пуст
