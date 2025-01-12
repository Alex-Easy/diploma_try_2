from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User, Contact, Shop, Category, Product, Basket, Order
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


# User Views
class UserRegisterView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        print(f"Verification token sent to {user.email}: {user.email_verification_token}")


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
                print(f"Password reset token for {email}: {token}")
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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)


# Shop Views
class ShopListView(generics.ListAPIView):
    queryset = Shop.objects.all()
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
        items = request.data.get('items', [])
        for item in items:
            Basket.objects.create(
                user=request.user,
                product_id=item['product_info'],
                quantity=item['quantity']
            )
        return Response({"message": "Items added to basket."}, status=201)

    def put(self, request):
        items = request.data.get('items', [])
        for item in items:
            basket_item = Basket.objects.get(id=item['id'], user=request.user)
            basket_item.quantity = item['quantity']
            basket_item.save()
        return Response({"message": "Basket updated."})

    def delete(self, request):
        item_ids = request.data.get('items', [])
        Basket.objects.filter(id__in=item_ids, user=request.user).delete()
        return Response({"message": "Items removed from basket."})


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

        with open(os.path.join(settings.BASE_DIR, 'data', url), 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)

        shop_name = data['shop']
        categories = data['categories']
        products = data['goods']

        shop, _ = Shop.objects.update_or_create(name=shop_name)

        for category in categories:
            Category.objects.update_or_create(
                id=category['id'], defaults={"name": category['name']}
            )

        for product in products:
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
