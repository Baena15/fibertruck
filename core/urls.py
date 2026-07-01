"""
FiberTruck - Auth URLs
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView, RegisterView, UserProfileView,
    user_me, change_password, list_technicians, api_info
)

urlpatterns = [
    path('', api_info, name='api-info'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/me/', user_me, name='user-me'),
    path('auth/profile/', UserProfileView.as_view(), name='user-profile'),
    path('auth/change-password/', change_password, name='change-password'),
    path('auth/technicians/', list_technicians, name='list-technicians'),
]
