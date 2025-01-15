from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from typing import Optional
import uuid


class CustomUserManager(BaseUserManager):
    """
    Custom user manager with email as the unique identifier.
    """
    def create_user(self, email: str, password: Optional[str] = None, **extra_fields) -> 'User':
        """
        Creates and returns a regular user.
        """
        if not email:
            raise ValueError("The Email field is required.")
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: Optional[str] = None, **extra_fields) -> 'User':
        """
        Creates and returns a superuser.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model using email as the unique identifier.
    """
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def generate_email_verification_token(self) -> str:
        """
        Generates an email verification token.
        """
        self.email_verification_token = uuid.uuid4().hex
        self.save()
        return self.email_verification_token

    def reset_password_token(self) -> str:
        """
        Generates a password reset token.
        """
        self.password_reset_token = uuid.uuid4().hex
        self.save()
        return self.password_reset_token

    def __str__(self) -> str:
        return self.email


class Contact(models.Model):
    """
    User contact information.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    house = models.CharField(max_length=10)
    structure = models.CharField(max_length=10, blank=True, null=True)
    building = models.CharField(max_length=10, blank=True, null=True)
    apartment = models.CharField(max_length=10, blank=True, null=True)
    phone = models.CharField(max_length=20)

    def __str__(self) -> str:
        return f"{self.city}, {self.street}, {self.house}"


class Shop(models.Model):
    """
    Shop model.
    """
    name = models.CharField(max_length=255, unique=True)
    url = models.URLField(blank=True, null=True)
    state = models.BooleanField(default=True)

    class Meta:
        ordering = ['id']

    def __str__(self) -> str:
        return self.name


class Category(models.Model):
    """
    Product category.
    """
    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ['id']

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    """
    Product model.
    """
    id = models.PositiveIntegerField(primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')
    model = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_rrc = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    parameters = models.JSONField(default=dict)

    class Meta:
        ordering = ['id']

    def __str__(self) -> str:
        return self.name


class Basket(models.Model):
    """
    User's shopping basket.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='basket')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='basket_items')
    quantity = models.PositiveIntegerField()

    def __str__(self) -> str:
        return f"Basket item: {self.product.name} (x{self.quantity})"


class Order(models.Model):
    """
    User's order.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=50, default='created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Order #{self.id} - {self.status}"
