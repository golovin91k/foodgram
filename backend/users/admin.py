from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AbstractUser

UserAdmin.fieldsets += (
    ('Extra Fields', {'fields': ('avatar', 'subscriptions')}),
)
admin.site.register(AbstractUser, UserAdmin)
