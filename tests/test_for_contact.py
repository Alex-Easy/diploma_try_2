# import pytest
# from django.contrib.auth import get_user_model
# from django.urls import reverse
# from rest_framework.test import APIClient  # Не забываем импортировать APIClient
# from procurement.models import Contact
#
# User = get_user_model()
#
#
# @pytest.fixture
# def api_client():
#     return APIClient()
#
#
# # Тест успешного создания контакта
# @pytest.mark.django_db
# def test_create_contact_success(api_client):
#     user = User.objects.create_user(email="test@example.com", password="password123")
#     api_client.force_authenticate(user=user)
#
#     data = {
#         "city": "Test City",
#         "street": "Test Street",
#         "house": "123",
#         "phone": "1234567890"
#     }
#
#     response = api_client.post(reverse('contact-list'), data, format='json')
#     print(f"Status code: {response.status_code}")
#     print(f"Response data: {response.data}")  # Диагностический вывод
#
#     assert response.status_code == 201
#     assert Contact.objects.filter(user=user, city="Test City").exists()
#
#
# # Тест получения списка контактов текущего пользователя
# @pytest.mark.django_db
# def test_get_contact_list(api_client):
#     user = User.objects.create_user(email="test@example.com", password="password123")
#     api_client.force_authenticate(user=user)
#
#     # Создаем два контакта для текущего пользователя
#     Contact.objects.create(user=user, city="City1", street="Street1", house="1", phone="1234567890")
#     Contact.objects.create(user=user, city="City2", street="Street2", house="2", phone="0987654321")
#
#     # Выполняем GET-запрос к API
#     response = api_client.get(reverse('contact-list'))
#     print(f"Response data: {response.data}")  # Диагностический вывод для проверки формата ответа
#
#     # Проверяем, что ответ успешный
#     assert response.status_code == 200
#
#     # Проверяем количество объектов в метаинформации и в results
#     assert response.data['count'] == 2  # Общее количество объектов
#     assert len(response.data['results']) == 2  # Количество объектов в текущей странице
#
#
# # Тест обновления контакта текущего пользователя
# @pytest.mark.django_db
# def test_update_contact(api_client):
#     user = User.objects.create_user(email="test@example.com", password="password123")
#     api_client.force_authenticate(user=user)
#
#     contact = Contact.objects.create(user=user, city="Old City", street="Old Street", house="1", phone="1234567890")
#     data = {
#         "city": "New City",
#         "street": "New Street",
#         "house": "2",
#         "phone": "0987654321"
#     }
#
#     response = api_client.put(reverse('contact-detail', args=[contact.id]), data, format='json')
#     assert response.status_code == 200
#
#     contact.refresh_from_db()
#     assert contact.city == "New City"
#     assert contact.street == "New Street"
#     assert contact.house == "2"
#     assert contact.phone == "0987654321"
#
#
# # Тест удаления контакта текущего пользователя
# @pytest.mark.django_db
# def test_delete_contact(api_client):
#     user = User.objects.create_user(email="test@example.com", password="password123")
#     api_client.force_authenticate(user=user)
#
#     contact = Contact.objects.create(user=user, city="City", street="Street", house="1", phone="1234567890")
#
#     response = api_client.delete(reverse('contact-detail', args=[contact.id]))
#     assert response.status_code == 204
#     assert not Contact.objects.filter(id=contact.id).exists()
#
#
# # Тест попытки работы с чужими контактами (ошибка доступа)
# @pytest.mark.django_db
# def test_access_foreign_contact(api_client):
#     user1 = User.objects.create_user(email="user1@example.com", password="password123")
#     user2 = User.objects.create_user(email="user2@example.com", password="password123")
#     api_client.force_authenticate(user=user1)
#
#     contact = Contact.objects.create(user=user2, city="City", street="Street", house="1", phone="1234567890")
#
#     # Попытка обновления чужого контакта
#     data = {
#         "city": "Unauthorized City",
#         "street": "Unauthorized Street",
#         "house": "999",
#         "phone": "0000000000"
#     }
#     response = api_client.put(reverse('contact-detail', args=[contact.id]), data, format='json')
#     assert response.status_code == 403
#
#     # Попытка удаления чужого контакта
#     response = api_client.delete(reverse('contact-detail', args=[contact.id]))
#     assert response.status_code == 403
#
