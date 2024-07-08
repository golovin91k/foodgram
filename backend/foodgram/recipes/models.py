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
    ingredients = models.ManyToManyField(Ingredient,
                                         through='IngredientInRecipe',
                                         through_fields=(
                                             'recipe', 'ingredient'),
                                         related_name='ingredients')
    name = models.CharField(max_length=256)
    image = models.ImageField(upload_to='recipes/images')
    text = models.TextField()
    cooking_time = models.IntegerField()
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-pub_date']


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='recipes')
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name='ingredient')
    amount = models.IntegerField()


class FavoriteRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorite_recipe')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorite')


class ShoppingCart(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='shopcart_recipe')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes_in_shopcart')


class Subscription(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscribers')
    subscriber = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='authors')


class ShortLink(models.Model):
    recipe = models.OneToOneField(
        Recipe, on_delete=models.CASCADE,
        related_name='shortlink', unique=True)
    shortlink = models.CharField(max_length=50, unique=True)
