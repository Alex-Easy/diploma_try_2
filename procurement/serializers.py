from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Contact, Shop, Category, Product, Basket, Order


# User Serializers
class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'company', 'position']

    def validate_email(self, value: str) -> str:
        """
        Ensure the email is unique.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data: dict) -> User:
        """
        Create a new user and generate an email verification token.
        """
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
    """
    Serializer for email verification.
    """
    email = serializers.EmailField()
    token = serializers.CharField()


class UserLoginSerializer(TokenObtainPairSerializer):
    """
    Custom serializer for user login with JWT tokens.
    """
    @classmethod
    def get_token(cls, user: User) -> 'Token':
        token = super().get_token(user)
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        return token


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for password reset requests.
    """
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset.
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    token = serializers.CharField()


class UserEditSerializer(serializers.ModelSerializer):
    """
    Serializer for editing user details.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'company', 'position']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'email': {'required': False},
        }

    def update(self, instance: User, validated_data: dict) -> User:
        """
        Update user details.
        """
        password = validated_data.pop('password', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


# Contact Serializers
class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer for user contacts.
    """
    class Meta:
        model = Contact
        fields = '__all__'
        extra_kwargs = {
            'user': {'read_only': True},
        }

    def validate_user(self, value: User) -> User:
        """
        Validate that the contact belongs to the current user.
        """
        if self.context['request'].user != value:
            raise serializers.ValidationError("You cannot create a contact for another user.")
        return value


# Shop, Category, Product Serializers
class ShopSerializer(serializers.ModelSerializer):
    """
    Serializer for shops.
    """
    class Meta:
        model = Shop
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for categories.
    """
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for products.
    """
    category = CategorySerializer(read_only=True)
    shop = ShopSerializer(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'


# Basket Serializers
class BasketSerializer(serializers.ModelSerializer):
    """
    Serializer for basket items.
    """
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Basket
        fields = ['id', 'user', 'product', 'quantity']

    def validate_quantity(self, value: int) -> int:
        """
        Ensure the quantity is greater than zero.
        """
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


# Order Serializers
class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for orders.
    """
    contact = serializers.PrimaryKeyRelatedField(queryset=Contact.objects.all())

    class Meta:
        model = Order
        fields = ['id', 'user', 'contact', 'status', 'created_at']
        read_only_fields = ['user', 'status', 'created_at']

    def create(self, validated_data: dict) -> Order:
        """
        Create a new order and associate it with the current user.
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
