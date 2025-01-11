import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


# Тест для успешной регистрации пользователя
@pytest.mark.django_db
def test_user_registration(api_client):
    # Данные для регистрации пользователя
    data = {
        "email": "test@example.com",  # Используем email как username
        "password": "testpassword123",
        "company": "Test Company",
        "position": "Test Position"
    }

    # URL для регистрации
    register_url = reverse('user-register')

    # Выполнение POST-запроса для регистрации
    response = api_client.post(register_url, data, format='json')

    # Проверка статуса ответа (должен быть 201 Created)
    assert response.status_code == 201

    # Проверка, что пользователь создан в базе данных
    user = User.objects.get(email="test@example.com")
    assert user.username == "test@example.com"  # Проверка, что username = email
    assert user.company == "Test Company"
    assert user.position == "Test Position"

    # Проверка, что пароль хэширован
    assert user.check_password("testpassword123")


# Тест для регистрации с уже существующей электронной почтой
@pytest.mark.django_db
def test_user_registration_duplicate_email(api_client):
    existing_user = User.objects.create_user(
        email="test@example.com",  # Указываем email
        username="test@example.com",  # Указываем username = email
        password="existingpassword123"
    )

    data = {
        "email": "test@example.com",  # Тот же email
        "password": "testpassword123",
        "company": "Test Company",
        "position": "Test Position"
    }

    # URL для регистрации
    register_url = reverse('user-register')

    # Выполнение POST-запроса для регистрации
    response = api_client.post(register_url, data, format='json')

    # Ожидаем статус 400 Bad Request
    assert response.status_code == 400

    # Проверяем, что ошибка связана с email
    assert "email" in response.data
    assert response.data["email"][0] == "Пользователь с таким email уже существует."

    # Проверяем, что в базе данных остался только один пользователь с этим email
    users_with_email = User.objects.filter(email="test@example.com")
    assert users_with_email.count() == 1  # Должен быть только один пользователь
    assert users_with_email.first().email == "test@example.com"  # Проверяем email
