from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .permissions import UserPermissions
from .serializers import EmailPasswordPasswordSerializer
from .models import User


@api_view(['POST'])
@permission_classes([UserPermissions])
def login(request):
    serializer = EmailPasswordPasswordSerializer(
        data=request.data  # , context=request
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.validated_data.get('user')
    # print('view_user:', user)
    token, created = Token.objects.get_or_create(user=user)
    return Response({'auth_token': token.key})


@api_view(['POST'])
def logout(request):
    # print()
    # print(request.user)
    # print(id(request.user))
    # user = User.objects.get(pk=request.user.id)
    # print(id(user))
    # print()
    if request.user.is_authenticated:
        # print('token', Token.objects.get(user=request.user))
        # print('token', Token.objects.get(user=user))
        Token.objects.get(user=request.user).delete()

    return Response()
