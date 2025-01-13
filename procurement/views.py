from rest_framework import generics, status, permissions
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User, Contact, Shop, Category, Product, Basket, Order
from rest_framework.exceptions import PermissionDenied
from .serializers import (
    UserRegisterSerializer, EmailVerificationSerializer,
    UserLoginSerializer, PasswordResetSerializer,
    PasswordResetConfirmSerializer, UserEditSerializer,
    ContactSerializer, ShopSerializer, CategorySerializer,
    ProductSerializer, BasketSerializer, OrderSerializer
)
import yaml
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


# User Views
class UserRegisterView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        logger.info(f"Verification token sent to {user.email}: {user.email_verification_token}")


class EmailVerificationView(APIView):
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            token = serializer.validated_data['token']
            try:
                user = User.objects.get(email=email)
                if user.email_verification_token == token:
                    user.email_verified = True
                    user.email_verification_token = None
                    user.save()
                    logger.info(f"User {email} verified their email.")
                    return Response({"message": "Email verified successfully."}, status=200)
                return Response({"error": "Invalid token."}, status=400)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=404)
        return Response(serializer.errors, status=400)


class UserLoginView(TokenObtainPairView):
    serializer_class = UserLoginSerializer


class PasswordResetView(APIView):
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                token = user.reset_password_token()
                logger.info(f"Password reset token for {email}: {token}")
                return Response({"message": "Password reset email sent."}, status=200)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=404)
        return Response(serializer.errors, status=400)


class PasswordResetConfirmView(APIView):
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            token = serializer.validated_data['token']
            password = serializer.validated_data['password']
            try:
                user = User.objects.get(email=email)
                if user.password_reset_token == token:
                    user.set_password(password)
                    user.password_reset_token = None
                    user.save()
                    logger.info(f"User {email} successfully reset their password.")
                    return Response({"message": "Password reset successfully."}, status=200)
                return Response({"error": "Invalid token."}, status=400)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=404)
        return Response(serializer.errors, status=400)


class UserEditView(generics.RetrieveUpdateAPIView):
    serializer_class = UserEditSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ContactListView(generics.ListCreateAPIView):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)  # Связываем контакт с текущим пользователем

    def get_queryset(self):
        # Добавляем сортировку по id или другому подходящему полю
        return Contact.objects.filter(user=self.request.user).order_by('id')


class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.all()  # Получаем все объекты (фильтруем доступ ниже)

    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user:
            raise PermissionDenied("Вы не имеете права доступа к этому контакту.")  # Возвращаем 403
        return obj


# Shop Views
class ShopListView(ListAPIView):
    queryset = Shop.objects.filter(state=True)  # Фильтруем только активные магазины
    serializer_class = ShopSerializer


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.all()
        shop_id = self.request.query_params.get('shop_id')
        category_id = self.request.query_params.get('category_id')
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset


# Basket Views
class BasketView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        basket = Basket.objects.filter(user=request.user)
        serializer = BasketSerializer(basket, many=True)
        return Response(serializer.data)

    def post(self, request):
        try:
            product_id = request.data.get('product')
            quantity = request.data.get('quantity')

            if not product_id or not quantity:
                return Response({"error": "Product and quantity are required."}, status=400)

            product = Product.objects.get(id=product_id)

            if quantity > product.quantity:
                return Response({"error": f"Not enough stock for product {product.id}"}, status=400)

            basket_item, created = Basket.objects.get_or_create(
                user=request.user,
                product=product,
                defaults={'quantity': quantity}
            )

            if not created:
                basket_item.quantity += quantity
                basket_item.save()

            return Response({"message": "Item added to basket."}, status=201)

        except Product.DoesNotExist:
            return Response({"error": f"Product with id {product_id} not found."}, status=404)

    def put(self, request):
        items = request.data.get('items', [])
        for item in items:
            try:
                basket_item = Basket.objects.get(id=item['id'], user=request.user)
                product = basket_item.product

                # Проверяем, достаточно ли товара на складе
                if item['quantity'] > product.quantity:
                    return Response({"error": f"Not enough stock for product {product.id}"}, status=400)

                basket_item.quantity = item['quantity']
                basket_item.save()
            except Basket.DoesNotExist:
                return Response({"error": f"Basket item with id {item['id']} not found."}, status=404)

        return Response({"message": "Basket updated."}, status=200)

    def delete(self, request):
        item_ids = request.data.get('items', [])
        basket_items = Basket.objects.filter(id__in=item_ids, user=request.user)

        if not basket_items.exists():
            return Response({"error": "Basket items not found."}, status=400)

        basket_items.delete()
        return Response({"message": "Items removed from basket."}, status=200)


# Order Views
class OrderListView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Partner Views
class PartnerUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        url = request.data.get('url')
        if not url:
            return Response({"error": "URL is required."}, status=400)

        file_path = os.path.join(settings.BASE_DIR, 'data', url)
        if not os.path.exists(file_path):
            return Response({"error": "File not found."}, status=404)

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")
            return Response({"error": "Invalid YAML file format."}, status=400)

        shop_name = data['shop']
        categories = data['categories']
        products = data['goods']

        shop, _ = Shop.objects.update_or_create(name=shop_name)

        for category in categories:
            Category.objects.update_or_create(
                id=category['id'], defaults={"name": category['name']}
            )

        for product in products:
            try:
                category = Category.objects.get(id=product['category'])
                Product.objects.update_or_create(
                    id=product['id'],
                    defaults={
                        "category": category,
                        "shop": shop,
                        "model": product['model'],
                        "name": product['name'],
                        "price": product['price'],
                        "price_rrc": product['price_rrc'],
                        "quantity": product['quantity'],
                        "parameters": product.get('parameters', {}),
                    },
                )
            except Category.DoesNotExist:
                return Response({"error": f"Category with id {product['category']} not found."}, status=404)

        return Response({"message": "Partner's price list updated successfully."})


class PartnerStateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        shop = Shop.objects.first()
        if not shop:
            return Response({"error": "No shop found."}, status=404)
        return Response({"name": shop.name, "state": shop.state})

    def post(self, request):
        state = request.data.get('state')
        if state not in ['on', 'off']:
            return Response({"error": "Invalid state."}, status=400)

        shop = Shop.objects.first()
        if not shop:
            return Response({"error": "No shop found."}, status=404)

        shop.state = state == 'on'
        shop.save()
        return Response({"message": "Partner state updated successfully."})


class PartnerOrdersView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(contact__isnull=False)
