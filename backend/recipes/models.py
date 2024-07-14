from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Tag(models.Model):
    """Модель тэга."""
    name = models.CharField('Название', max_length=32, unique=True)
    slug = models.SlugField('Слаг', max_length=32, unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField('Название', max_length=128)
    measurement_unit = models.CharField('Единица измерения',
                                        max_length=64)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


class Recipe(models.Model):
    """Модель рецепта."""
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes',
        verbose_name='Авторы')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='IngredientInRecipe',
                                         through_fields=(
                                             'recipe', 'ingredient'),
                                         related_name='ingredients',
                                         verbose_name='Ингредиенты')
    name = models.CharField('Название', max_length=256)
    image = models.ImageField(upload_to='recipes/images',
                              verbose_name='Изображение')
    text = models.TextField('Описание')
    cooking_time = models.IntegerField('Время приготовления')
    pub_date = models.DateTimeField('Дата публикации',
                                    auto_now_add=True)

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class IngredientInRecipe(models.Model):
    """Модель, позволяющая связать рецепт и ингредиент для рецепта."""
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='recipes')
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name='ingredient')
    amount = models.IntegerField()

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'


class FavoriteRecipe(models.Model):
    """Модель израбранного рецапта."""
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorite_recipe',
        verbose_name='Рецепты')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorite',
        verbose_name='Пользователи')

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class ShoppingCart(models.Model):
    """Модель списка покупок."""
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='shopcart_recipe',
        verbose_name='Рецепты')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes_in_shopcart',
        verbose_name='Пользователи')

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


class ShortLink(models.Model):
    """Модель короткой ссылки на рецепт."""
    recipe = models.OneToOneField(
        Recipe, on_delete=models.CASCADE,
        related_name='shortlink', unique=True, verbose_name='Рецепт')
    shortlink = models.CharField(
        max_length=50, unique=True, verbose_name='Уникальная ссылка')

    class Meta:
        verbose_name = 'Короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'
