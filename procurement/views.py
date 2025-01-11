from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import UserRegisterSerializer


class UserRegisterView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"message": "Пользователь успешно зарегистрирован."}, status=status.HTTP_201_CREATED)
