"""
FiberTruck - Auth Views & Permissions
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from .serializers import (
    CustomTokenObtainPairSerializer, UserSerializer,
    RegisterSerializer, PasswordChangeSerializer
)


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'admin'


class IsSupervisor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['admin', 'supervisor']


class IsTechnician(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['admin', 'supervisor', 'technician']


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_me(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    serializer = PasswordChangeSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Contrasena actual incorrecta'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Contrasena actualizada correctamente'})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsSupervisor])
def list_technicians(request):
    techs = User.objects.filter(role='technician')
    serializer = UserSerializer(techs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_info(request):
    return Response({
        'name': 'FiberTruck API',
        'version': '1.0',
        'description': 'API de diagnostico FTTH para Cieza, Murcia',
        'endpoints': {
            'auth': {
                'login': 'POST /api/auth/login/',
                'refresh': 'POST /api/auth/token/refresh/',
                'register': 'POST /api/auth/register/',
                'me': 'GET /api/auth/me/',
            },
            'network': {
                'zones': 'GET /api/zones/',
                'boxes': 'GET /api/boxes/',
                'clients': 'GET /api/clients/',
                'incidents': 'GET /api/incidents/',
                'diagnose': 'POST /api/clients/report_outage/',
            }
        }
    })
