"""
FiberTruck - Admin Configuration
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'zone_assigned', 'is_available', 'is_staff']
    list_filter = ['role', 'is_available', 'is_staff', 'created_at']
    fieldsets = UserAdmin.fieldsets + (
        ('FiberTruck', {'fields': ('role', 'phone', 'zone_assigned', 'is_available')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('FiberTruck', {'fields': ('role', 'phone', 'zone_assigned')}),
    )
