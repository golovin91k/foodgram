from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .constans import (
    TAG_NAME_MAX_LENGTH, TAG_SLUG_MAX_LENGTH, INGREDIENT_NAME_MAX_LENGTH,
    INGREDIENT_MEAS_UNIT_MAX_LENGTH, RECIPE_NAME_MAX_LENGTH,
    SHORTLINK_MAX_LENTH
)
from .validators import validate_amount, validate_cooking_time


User = get_user_model()


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(
        'Название', max_length=TAG_NAME_MAX_LENGTH, unique=True)
    slug = models.SlugField(
        'Слаг', max_length=TAG_SLUG_MAX_LENGTH, unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField(
        'Название', max_length=INGREDIENT_NAME_MAX_LENGTH, unique=True)
    measurement_unit = models.CharField(
        'Единица измерения', max_length=INGREDIENT_MEAS_UNIT_MAX_LENGTH)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes',
        verbose_name='Авторы')
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientInRecipe',
        through_fields=('recipe', 'ingredient'),
        related_name='ingredients',
        verbose_name='Ингредиенты')
    name = models.CharField('Название', max_length=RECIPE_NAME_MAX_LENGTH)
    image = models.ImageField(
        upload_to='recipes/images',
        verbose_name='Изображение')
    text = models.TextField('Описание')
    cooking_time = models.IntegerField(
        'Время приготовления', validators=[validate_cooking_time])
    pub_date = models.DateTimeField(
        'Дата публикации', auto_now_add=True)

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    """Модель, позволяющая связать рецепт и ингредиент для рецепта."""
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='recipes')
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name='ingredient')
    amount = models.IntegerField(validators=[validate_amount])

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'


class RecipeUserBaseModel(models.Model):
    """Абстрактная модель рецепт-пользователь."""
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепты')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователи')

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'user'],
                                    name='unique_together')
        ]

    def __str__(self):
        return f'{self.recipe} - {self.user}'


class FavoriteRecipe(RecipeUserBaseModel):
    """Модель израбранного рецепта."""

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class ShoppingCart(RecipeUserBaseModel):
    """Модель списка покупок."""

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'


class Subscription(models.Model):
    """Модель подписки."""
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscribers',
        verbose_name='Авторы')
    subscriber = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sub_authors',
        verbose_name='Подписчики')

    class Meta:
        verbose_name = 'Список подписок'
        verbose_name_plural = 'Списки подписок'
        constraints = [
            models.UniqueConstraint(fields=['author', 'subscriber'],
                                    name='unique_favorite')
        ]

    def clean(self):
        if self.author == self.subscriber:
            raise ValidationError('Нельзя подписаться на самого себя.')

    def __str__(self):
        return f'{self.author} - {self.subscriber}'


class ShortLink(models.Model):
    """Модель короткой ссылки на рецепт."""
    recipe = models.OneToOneField(
        Recipe, on_delete=models.CASCADE,
        related_name='shortlink', unique=True, verbose_name='Рецепт')
    shortlink = models.CharField(
        max_length=SHORTLINK_MAX_LENTH, unique=True,
        verbose_name='Уникальная ссылка')

    class Meta:
        verbose_name = 'Короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'

    def __str__(self):
        return f'{self.recipe} - {self.shortlink}'
