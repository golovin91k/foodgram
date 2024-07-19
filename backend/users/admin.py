from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import AbstractUser

UserAdmin.fieldsets += (
    ('Extra Fields', {'fields': ('avatar',)}),
)
admin.site.register(AbstractUser, UserAdmin)
admin.site.unregister(Group)
