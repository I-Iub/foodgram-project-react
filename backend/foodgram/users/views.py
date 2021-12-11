from django.shortcuts import get_object_or_404
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.permissions import UserPermissions
from users.serializers import EmailPasswordSerializer


@api_view(['POST'])
@permission_classes([UserPermissions])
def login(request):
    serializer = EmailPasswordSerializer(
        data=request.data
    )
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data.get('user')
    token, created = Token.objects.get_or_create(user=user)
    return Response({'auth_token': token.key})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    token = get_object_or_404(Token, user=request.user)
    token.delete()
    return Response()
