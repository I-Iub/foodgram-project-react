from rest_framework import serializers

from .models import User


class EmailPasswordPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        is_user_exists = User.objects.filter(email=data.get('email')).exists()
        if not is_user_exists:
            raise serializers.ValidationError({
                'email': 'Неверно указан адрес электронной почты.'
            })
        user = User.objects.get(email=data.get('email'))
        if not user.check_password(data.get('password')):
            raise serializers.ValidationError({
                'password': 'Пароль неправильный.'
            })
        data['user'] = user
        return data
