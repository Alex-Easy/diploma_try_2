from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


# Кастомный менеджер пользователя
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)  # Устанавливаем username равным email
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


# Кастомная модель пользователя
class User(AbstractUser):
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)

    # Указываем кастомный менеджер
    objects = CustomUserManager()

    # Определяем, что email будет использоваться как основное поле для аутентификации
    USERNAME_FIELD = 'email'

    # Дополнительные обязательные поля, которые запрашиваются при создании суперпользователя
    REQUIRED_FIELDS = []  # Здесь можно указать 'first_name', 'last_name', если они должны быть обязательными

    def generate_email_verification_token(self):
        self.email_verification_token = uuid.uuid4().hex
        self.save()
        return self.email_verification_token

    def reset_password_token(self):
        self.password_reset_token = uuid.uuid4().hex
        self.save()
        return self.password_reset_token

    def __str__(self):
        return self.email


class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    house = models.CharField(max_length=10)
    structure = models.CharField(max_length=10, blank=True, null=True)
    building = models.CharField(max_length=10, blank=True, null=True)
    apartment = models.CharField(max_length=10, blank=True, null=True)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.city}, {self.street}, {self.house}"


class Shop(models.Model):
    name = models.CharField(max_length=255, unique=True)
    url = models.URLField(blank=True, null=True)
    state = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ['id']  # Добавляем сортировку по умолчанию

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')
    model = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_rrc = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    parameters = models.JSONField()

    def __str__(self):
        return self.name


class Basket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='basket')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='basket_items')
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"Basket item: {self.product.name} (x{self.quantity})"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=50, default='created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.status}"
