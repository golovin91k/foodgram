from django.contrib.auth.models import AbstractUser
from django.db import models


class MyUser(AbstractUser):
    email = models.EmailField(unique=True, blank=False)
    avatar = models.ImageField(
        upload_to='users', null=True, default=None)
    username = models.CharField(max_length=150, unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'password', 'username']
#    subscriptions = models.ManyToManyField(
#        'self', related_name='followers', symmetrical=False, blank=True)


class UserSubscriber(models.Model):
    user = models.ForeignKey(
        MyUser, on_delete=models.CASCADE, related_name="following")
    subscriber = models.ForeignKey(
        MyUser, on_delete=models.CASCADE, related_name="followers")
