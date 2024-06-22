from django.contrib.auth.models import AbstractUser
from django.db import models


class MyUser(AbstractUser):
    avatar = models.ImageField(blank=True, null=True)
    subscriptions = models.ManyToManyField(
        'self', related_name='followers', symmetrical=False, blank=True)


"""

    recipes = models.ForeignKey(Recipe, on_delete=models.SET_NULL, blank=True, null=True)
    recipes_count = models.IntegerField()
    favorite_recipes = models.ManyToManyField(Recipe, blank=True, null=True)
    shopping_cart = models.ManyToManyField(Recipe, blank=True, null=True)


class UserShopCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE)
"""
