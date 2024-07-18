from django.contrib.auth.models import AbstractUser
from django.db import models

from .constans import USERNAME_MAX_LENGTH


class AbstractUser(AbstractUser):
    """Модель пользователя."""
    email = models.EmailField(unique=True, blank=False)
    avatar = models.ImageField(
        upload_to='users', null=True, default=None)
    username = models.CharField(max_length=USERNAME_MAX_LENGTH, unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'password', 'username']

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
