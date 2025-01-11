from rest_framework import serializers
from .models import User


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'company', 'position']
        extra_kwargs = {
            'email': {'validators': []}  # Отключаем стандартные валидаторы
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value

    def create(self, validated_data):
        validated_data['username'] = validated_data['email']
        user = User.objects.create_user(
            username=validated_data['username'],  # Используем email как username
            email=validated_data['email'],
            password=validated_data['password'],
            company=validated_data.get('company', ''),
            position=validated_data.get('position', '')
        )
        return user
