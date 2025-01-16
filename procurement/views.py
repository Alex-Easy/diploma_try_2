from typing import Any
from django.db.models.query import QuerySet
from rest_framework import generics, status, permissions
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User, Contact, Shop, Category, Product, Basket, Order
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
import yaml
import os
from django.conf import settings
import logging
from .serializers import (
    UserRegisterSerializer, EmailVerificationSerializer,
    UserLoginSerializer, PasswordResetSerializer,
    PasswordResetConfirmSerializer, UserEditSerializer,
    ContactSerializer, ShopSerializer, CategorySerializer,
    ProductSerializer, BasketSerializer, OrderSerializer
)

logger = logging.getLogger(__name__)


# User Views
class UserRegisterView(generics.CreateAPIView):
    """
    View for user registration.
    """
    serializer_class = UserRegisterSerializer

    def perform_create(self, serializer: UserRegisterSerializer) -> None:
        user = serializer.save()
        logger.info(f"Verification token sent to {user.email}: {user.email_verification_token}")


class EmailVerificationView(APIView):
    """
    View for email verification.
    """
    def post(self, request: Any) -> Response:
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
    """
    View for user login.
    """
    serializer_class = UserLoginSerializer


class PasswordResetView(APIView):
    """
    View to handle password reset requests.
    """
    def post(self, request: Any) -> Response:
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
    """
    View to confirm password reset.
    """
    def post(self, request: Any) -> Response:
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
    """
    View for retrieving and updating user details.
    """
    serializer_class = UserEditSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self) -> User:
        return self.request.user


class ContactListView(generics.ListCreateAPIView):
    """
    View for listing and creating user contacts.
    """
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return Contact.objects.filter(user=self.request.user).order_by('id')

    def perform_create(self, serializer: ContactSerializer) -> None:
        serializer.save(user=self.request.user)


class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, updating, and deleting a specific contact.
    """
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return Contact.objects.all()

    def get_object(self) -> Contact:
        obj = super().get_object()
        if obj.user != self.request.user:
            raise PermissionDenied("You do not have permission to access this contact.")
        return obj


# Shop Views
class ShopListView(ListAPIView):
    """
    View for listing active shops.
    """
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer


class CategoryListView(generics.ListAPIView):
    """
    View for listing product categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductListView(generics.ListAPIView):
    """
    View for listing products with optional filtering by shop and category.
    """
    serializer_class = ProductSerializer

    def get_queryset(self) -> QuerySet:
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
    """
    View for managing the user's basket.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: Any) -> Response:
        basket = Basket.objects.filter(user=request.user)
        serializer = BasketSerializer(basket, many=True)
        return Response(serializer.data)

    def post(self, request: Any) -> Response:
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

    def put(self, request: Any) -> Response:
        """
        Update basket items quantity.
        """
        items = request.data.get('items', [])
        for item in items:
            try:
                basket_item = Basket.objects.get(id=item['id'], user=request.user)
                product = basket_item.product

                if item['quantity'] > product.quantity:
                    return Response({"error": f"Not enough stock for product {product.id}"}, status=400)

                basket_item.quantity = item['quantity']
                basket_item.save()
            except Basket.DoesNotExist:
                return Response({"error": f"Basket item with id {item['id']} not found."}, status=404)

        return Response({"message": "Basket updated successfully."}, status=200)

    def delete(self, request: Any) -> Response:
        """
        Remove items from the basket.
        """
        item_ids = request.data.get('items', [])
        basket_items = Basket.objects.filter(id__in=item_ids, user=request.user)

        if not basket_items.exists():
            return Response({"error": "Basket items not found."}, status=400)

        basket_items.delete()
        return Response({"message": "Items removed from basket."}, status=200)


# Order Views
class OrderListView(generics.ListCreateAPIView):
    """
    View for listing and creating orders.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer: OrderSerializer) -> None:
        """
        Create an order and clear the basket after reducing stock.
        """
        order = serializer.save(user=self.request.user)
        basket_items = Basket.objects.filter(user=self.request.user)

        if not basket_items.exists():
            raise serializers.ValidationError({"error": "Basket is empty, cannot create an order."})

        for basket_item in basket_items:
            product = basket_item.product
            if basket_item.quantity > product.quantity:
                raise serializers.ValidationError({"error": f"Not enough stock for product {product.name}."})

            product.quantity -= basket_item.quantity
            product.save()

        basket_items.delete()


# Partner Views
class PartnerUpdateView(APIView):
    """
    View for updating the partner's price list.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request: Any) -> Response:
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

        return Response({"message": "Partner's price list updated successfully."}, status=200)


class PartnerStateView(APIView):
    """
    View for retrieving and updating the partner's state.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: Any) -> Response:
        """
        Retrieve the partner's current state.
        """
        shop = Shop.objects.first()
        if not shop:
            return Response({"error": "No shop found."}, status=404)
        return Response({"name": shop.name, "state": shop.state})

    def post(self, request: Any) -> Response:
        """
        Update the partner's state.
        """
        state = request.data.get('state')
        if state not in ['on', 'off']:
            return Response({"error": "Invalid state. Use 'on' or 'off'."}, status=400)

        shop = Shop.objects.first()
        if not shop:
            return Response({"error": "No shop found."}, status=404)

        shop.state = state == 'on'
        shop.save()
        return Response({"message": "Partner state updated successfully."}, status=200)


class PartnerOrdersView(generics.ListAPIView):
    """
    View for listing partner's related orders.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self) -> QuerySet:
        return Order.objects.filter(contact__isnull=False)


class SupplierUploadPricelistView(APIView):
    """
    View for uploading supplier price lists.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request: Any, shop_id: int) -> Response:
        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            return Response({"error": f"Shop with id {shop_id} not found."}, status=404)

        if 'file' not in request.FILES:
            return Response({"error": "No file provided."}, status=400)

        uploaded_file = request.FILES['file']

        try:
            pricelist_data = yaml.safe_load(uploaded_file)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML: {e}")
            return Response({"error": "Invalid YAML file format."}, status=400)

        for item in pricelist_data:
            try:
                category_id = item.get('category')
                if not category_id:
                    return Response({"error": "Missing category ID in price list."}, status=400)

                category = Category.objects.get(id=category_id)
                Product.objects.update_or_create(
                    id=item.get('id'),
                    defaults={
                        'category': category,
                        'shop': shop,
                        'name': item.get('name'),
                        'model': item.get('model', ''),
                        'price': item.get('price'),
                        'price_rrc': item.get('price_rrc'),
                        'quantity': item.get('quantity'),
                        'parameters': item.get('parameters', {})
                    }
                )
            except Category.DoesNotExist:
                return Response({"error": f"Category with id {category_id} not found."}, status=404)

        return Response({"message": "Price list uploaded successfully."}, status=200)

