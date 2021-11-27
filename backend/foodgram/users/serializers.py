from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class EmailPasswordPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True)

    # def validate_email(self, value):
    #     is_user_exists = User.objects.filter(
    #         email=self.context.data.get('email')
    #     ).exists()
    #     if not is_user_exists:
    #         raise serializers.ValidationError(
    #             'Неверно указан адрес электронной почты.'
    #         )
    #     return value

    # def validate_password(self, value):  # повторяет то же что и в UserSerializer validate_password
    #     print(self.context.data.get('email'))
    #     # user = User.objects.get(email=self.context.data.get('email'))
    #     # if not user.check_password(value):
    #     #     raise serializers.ValidationError()
    #     return value

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
        # print('serializer_user:', user)
        data['user'] = user
        # print('serializer_data', data)
        return data

    # def validate_email(self, value):
    #     print('validate_email')
    #     return value

    # def validate_password(self, value):
    #     print('validate_password')
    #     return value

    # def validate(self, data):
    #     print('validate_object')
    #     return data
