from django.db import models

from users_shopcart_favorite.models import UserProfile


class Ingredient(models.Model):
    name = models.CharField(max_length=128)
    measurement_unit = models.CharField(max_length=64)


class Tag(models.Model):
    name = models.CharField(max_length=32, unique=True)
    slug = models.SlugField(max_length=32, unique=True)


class Recipe(models.Model):
    tags = models.ManyToManyField(Tag)
    author = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE)
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientinRecipe')
    name = models.CharField(max_length=256)
    image = models.ImageField(upload_to=None)
    text = models.TextField()
    cooking_time = models.IntegerField()


class IngredientinRecipe(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.IntegerField()
