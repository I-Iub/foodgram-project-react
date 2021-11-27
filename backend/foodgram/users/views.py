from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .permissions import UserPermissions
from .serializers import EmailPasswordPasswordSerializer


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
    return Response('logouttttttttttt')
