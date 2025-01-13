import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


# Test successful user registration
@pytest.mark.django_db
def test_user_registration_success(api_client):
    data = {
        "email": "test@example.com",
        "password": "securepassword123",
        "first_name": "John",
        "last_name": "Doe",
        "company": "Test Company",
        "position": "Developer"
    }
    response = api_client.post(reverse('user-register'), data, format='json')
    assert response.status_code == 201
    assert User.objects.filter(email="test@example.com").exists()


# Test user registration with duplicate email
@pytest.mark.django_db
def test_user_registration_duplicate_email(api_client):
    User.objects.create_user(email="test@example.com", password="password123")  # Теперь username не обязателен
    data = {
        "email": "test@example.com",
        "password": "securepassword123",
        "first_name": "John",
        "last_name": "Doe",
        "company": "Test Company",
        "position": "Developer"
    }
    response = api_client.post(reverse('user-register'), data, format='json')
    assert response.status_code == 400
    assert "email" in response.data


# Test user registration with invalid data
@pytest.mark.django_db
def test_user_registration_invalid_data(api_client):
    data = {
        "email": "invalid-email",  # incorrect email
        "password": "short",  # short password
        "first_name": "John",
        "last_name": "Doe",
        "company": "Test Company",
        "position": "Developer"
    }
    response = api_client.post(reverse('user-register'), data, format='json')

    # Check that the response status code is 400
    assert response.status_code == 400

    # Check that the response data contains the expected errors
    assert "email" in response.data  # Ошибка email
    assert response.data["email"][0].code == "invalid"  # Code exception email
    assert "password" in response.data  # Ошибка пароля
    assert response.data["password"][0].code == "password_too_short"  # Code exception password


# Test successful email verification
@pytest.mark.django_db
def test_email_verification_success(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    user.generate_email_verification_token()
    data = {
        "email": user.email,
        "token": user.email_verification_token
    }
    response = api_client.post(reverse('email-verification'), data, format='json')
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.email_verified is True


# Test email verification with invalid token
@pytest.mark.django_db
def test_email_verification_invalid_token(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    user.generate_email_verification_token()
    data = {
        "email": user.email,
        "token": "invalid-token"
    }
    response = api_client.post(reverse('email-verification'), data, format='json')
    assert response.status_code == 400


# Test email verification with nonexistent user
@pytest.mark.django_db
def test_email_verification_nonexistent_user(api_client):
    data = {
        "email": "nonexistent@example.com",
        "token": "some-token"
    }
    response = api_client.post(reverse('email-verification'), data, format='json')
    assert response.status_code == 404


# Test successful user login
@pytest.mark.django_db
def test_user_login_success(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    data = {
        "email": user.email,
        "password": "password123"
    }
    response = api_client.post(reverse('user-login'), data, format='json')
    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data


# Test user login with invalid password
@pytest.mark.django_db
def test_user_login_invalid_password(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    data = {
        "email": user.email,
        "password": "wrongpassword"
    }
    response = api_client.post(reverse('user-login'), data, format='json')
    assert response.status_code == 401


# Test password reset request
@pytest.mark.django_db
def test_password_reset_request_success(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    data = {
        "email": user.email
    }
    response = api_client.post(reverse('password-reset'), data, format='json')
    assert response.status_code == 200


# Test password reset request with nonexistent email
@pytest.mark.django_db
def test_password_reset_request_nonexistent_email(api_client):
    data = {
        "email": "nonexistent@example.com"
    }
    response = api_client.post(reverse('password-reset'), data, format='json')
    assert response.status_code == 404


# Test password reset confirmation
@pytest.mark.django_db
def test_password_reset_confirm_success(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    token = user.reset_password_token()
    data = {
        "email": user.email,
        "password": "newpassword123",
        "token": token
    }
    response = api_client.post(reverse('password-reset-confirm'), data, format='json')
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password("newpassword123")


# Test password reset confirmation with invalid token
@pytest.mark.django_db
def test_password_reset_confirm_invalid_token(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    data = {
        "email": user.email,
        "password": "newpassword123",
        "token": "invalid-token"
    }
    response = api_client.post(reverse('password-reset-confirm'), data, format='json')
    assert response.status_code == 400


# Test user profile update
@pytest.mark.django_db
def test_user_profile_update_success(api_client):
    # Создаем пользователя
    user = User.objects.create_user(email="test@example.com", password="password123")

    # Аутентифицируем пользователя
    api_client.force_authenticate(user=user)

    # Данные для обновления
    data = {
        "first_name": "Updated",
        "last_name": "User",
        "company": "Updated Company",
        "position": "Updated Position"
    }

    # Отправляем запрос на обновление
    response = api_client.put(reverse('user-edit'), data, format='json')

    # Диагностический вывод (на случай ошибок)
    print(response.data)

    # Проверяем, что статус 200 (OK)
    assert response.status_code == 200

    # Проверяем, что данные обновлены в базе данных
    user.refresh_from_db()
    assert user.first_name == "Updated"
    assert user.last_name == "User"
    assert user.company == "Updated Company"
    assert user.position == "Updated Position"


# Test user profile update with invalid data
@pytest.mark.django_db
def test_user_profile_update_invalid_data(api_client):
    user = User.objects.create_user(email="test@example.com", password="password123")
    api_client.force_authenticate(user=user)
    data = {
        "email": "invalid-email"
    }
    response = api_client.put(reverse('user-edit'), data, format='json')
    assert response.status_code == 400
    assert "email" in response.data
