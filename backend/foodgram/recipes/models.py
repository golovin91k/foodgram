from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=32, unique=True)
    slug = models.SlugField(max_length=32, unique=True)


class Ingredient(models.Model):
    name = models.CharField(max_length=128)
    measurement_unit = models.CharField(max_length=64)


class Recipe(models.Model):
    tags = models.ManyToManyField(Tag)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes')
    ingredients = models.ManyToManyField(Ingredient, through='IngredientInRecipe',
                                         through_fields=('recipe', 'ingredient'),
                                         related_name='ingredients')
    name = models.CharField(max_length=256)
    image = models.ImageField(upload_to='recipes/images')
    text = models.TextField()
    cooking_time = models.IntegerField()


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='recipes')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='in22gredient')
    amount = models.IntegerField()


"""
class UserRecipe(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, )
    recipes = models.ForeignKey(Recipe, on_delete=models.SET_NULL, blank=True,
                                null=True, related_name='user_recipes')
    recipes_count = models.IntegerField()
    favorite_recipes = models.ManyToManyField(
        Recipe, blank=True, related_name='user_favorite_recipes')
    shopping_cart = models.ManyToManyField(
        Recipe, blank=True, related_name='user_shopping_cart')
"""
