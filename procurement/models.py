from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)

    def generate_email_verification_token(self):
        self.email_verification_token = uuid.uuid4().hex
        self.save()
        return self.email_verification_token

    def reset_password_token(self):
        self.password_reset_token = uuid.uuid4().hex
        self.save()
        return self.password_reset_token

    def __str__(self):
        return self.username


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
