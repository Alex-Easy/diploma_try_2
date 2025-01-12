from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Contact, Shop, Category, Product, Basket, Order


# User Serializers
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'company', 'position']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            company=validated_data.get('company', ''),
            position=validated_data.get('position', '')
        )
        user.generate_email_verification_token()
        return user


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField()


class UserLoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        return token


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    token = serializers.CharField()


class UserEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'company', 'position']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


# Contact Serializers
class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'

    def validate_user(self, value):
        if self.context['request'].user != value:
            raise serializers.ValidationError("Нельзя создать контакт для другого пользователя.")
        return value


# Shop, Category, Product Serializers
class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    shop = ShopSerializer(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'


# Basket Serializers
class BasketSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Basket
        fields = ['id', 'user', 'product', 'quantity']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Количество должно быть больше нуля.")
        return value


# Order Serializers
class OrderSerializer(serializers.ModelSerializer):
    contact = ContactSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'contact', 'status', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
