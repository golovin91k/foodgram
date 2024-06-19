from django.db import models
from django.contrib.auth.models import User

from recipes.models import Recipe


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    avatar = models.ImageField(blank=True, null=True)
    subscriptions = models.ManyToManyField(
        'self', related_name='followers', symmetrical=False)
    recipes = models.ForeignKey(Recipe, on_delete=models.SET_NULL)
    favorite_recipes = models.ManyToManyField(
        Recipe, on_delete=models.SET_NULL)
    recipes_count = models.IntegerField()


class UserShopCart(models.Model):
    user = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE)
