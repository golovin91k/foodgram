import base64
import re

from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import (
    Recipe, Tag, Ingredient, IngredientInRecipe,
    FavoriteRecipe, Subscription, ShoppingCart, )
from .utils import create_shortlink
from recipes.validators import validate_cooking_time, validate_amount


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Вспомогательный сериализатор для обработки изображения."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class SpecialUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания объекта пользователя."""
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password')
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
        }

    def validate_username(self, value):
        if not re.match(r'^[\w.@+-]+\Z', value):
            raise serializers.ValidationError({'Некорректный юзернейм'})
        return value


class SpecialUserSerializer(UserSerializer):
    """Сериализатор для просмотра объекта пользователя."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        current_user = self.context['request'].user
        return (
            current_user.is_authenticated and current_user != obj
            and obj.subscribers.filter(subscriber=current_user).exists())


class AvatarSerializer(serializers.Serializer):
    """Сериализатор для создания и изменения аватара пользователя."""
    avatar = Base64ImageField()

    def save(self, instance, validated_data):
        instance.avatar = self.validated_data['avatar']
        instance.save()
        return instance


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля пользователя."""
    new_password = serializers.CharField()
    current_password = serializers.CharField()

    def save(self, instance, validated_data):
        if not instance.check_password(validated_data['current_password']):
            raise serializers.ValidationError(
                {'Введен неверный текущий пароль'})
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента."""
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор количества ингредиента в рецепте.
    Сериализатор используется при чтении рецепта.
    """
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True)

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор количества ингредиента в рецепте.
    Сериализатор используется при создании и редактировании рецепта.
    """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(validators=[validate_amount])

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeGetSerializer(serializers.ModelSerializer):
    """Сериалиазатор чтения рецепта."""
    tags = TagSerializer(many=True)
    image = Base64ImageField()
    author = SpecialUserSerializer(read_only=True)
    ingredients = IngredientInRecipeGetSerializer(
        many=True, read_only=True, source='recipes')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        current_user = self.context['request'].user
        return (
            current_user.is_authenticated
            and current_user.favoriterecipe_set.all().filter(
                recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        current_user = self.context['request'].user
        return (
            current_user.is_authenticated
            and current_user.shoppingcart_set.all().filter(
                recipe=obj).exists())


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания и изменения рецепта."""
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    image = Base64ImageField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    ingredients = IngredientInRecipeCreateSerializer(many=True)
    cooking_time = serializers.IntegerField(validators=[validate_cooking_time])

    class Meta:
        model = Recipe
        fields = (
            'tags', 'author', 'name', 'image',
            'text', 'cooking_time', 'ingredients')

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы один тэг.'
            )
        tag_list = []
        for tag_obj in value:
            if tag_obj in tag_list:
                raise serializers.ValidationError(
                    'В рецепт нельзя добавлять одинаковые тэги')
            tag_list.append(tag_obj)
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы один ингредиент'
            )
        ingredient_list = []
        for ingr_obj in value:
            if ingr_obj in ingredient_list:
                raise serializers.ValidationError(
                    'В рецепт нельзя добавлять одинаковые ингредиенты.')
            ingredient_list.append(ingr_obj)
        return value

    def create_ingredients_for_recipe(self, recipe, ingredients):
        ingredients_list = []
        for ingredient in ingredients:
            ingredients_list.append(IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']))
        IngredientInRecipe.objects.bulk_create(ingredients_list)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        recipe.save()
        self.create_ingredients_for_recipe(
            recipe=recipe, ingredients=ingredients)
        create_shortlink(recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        super(RecipeCreateSerializer, self).update(instance, validated_data)
        instance.tags.set(tags)
        IngredientInRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients_for_recipe(
            recipe=instance, ingredients=ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeGetSerializer(instance, context=self.context).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор краткого представления рецепта."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    image = Base64ImageField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class SubscribeReturnSerializer(SpecialUserSerializer):
    """
    Сериализатор для отображения объекта пользователя после
    создания подписки на этого пользователя.
    """
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar')

    def get_recipes(self, obj):
        author_recipes = Recipe.objects.filter(author=obj)
        request_recipes_limit = self.context.get('request').GET
        recipes_limit = request_recipes_limit.get('recipes_limit')
        try:
            if recipes_limit is not None and isinstance(
                    int(recipes_limit), int):
                author_recipes = author_recipes[:int(recipes_limit)]
        except ValueError:
            raise serializers.ValidationError(
                'Значение recipes_limit должно быть числом.')
        return ShortRecipeSerializer(
            author_recipes, many=True, read_only=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class SubscribeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания подписки на пользователя."""
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    subscriber = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Subscription
        fields = ('author', 'subscriber')

    def validate(self, data):
        author = data['author']
        subscriber = self.context['request'].user
        if author == subscriber:
            raise serializers.ValidationError(
                {'Нельзя подписаться на самого себя'})
        if subscriber.sub_authors.all().filter(author=author).exists():
            raise ValidationError({'Вы уже подписаны на этого пользователя'})
        return data

    def create(self, validated_data):
        return Subscription.objects.create(**validated_data)

    def to_representation(self, instance):
        return SubscribeReturnSerializer(
            instance.author, context=self.context).data


class ShoppingCartCreateSerializer(serializers.ModelSerializer):
    """Сериализатор добавления рецепта в список покупок."""
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ('recipe', 'user')

    def validate(self, data):
        user = self.context['request'].user
        if user.shoppingcart_set.all().filter(recipe=data['recipe']).exists():
            raise ValidationError(
                {'Этот рецепт уже добавлен в список покупок.'})
        return data

    def create(self, validated_data):
        return ShoppingCart.objects.create(**validated_data)

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe, context=self.context).data


class FavoriteRecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор добавления рецепта в избранное."""
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = FavoriteRecipe
        fields = ('recipe', 'user')

    def validate(self, data):
        user = self.context['request'].user
        if user.favoriterecipe_set.all().filter(
                recipe=data['recipe']).exists():
            raise ValidationError(
                {'Этот рецепт уже добавлен в избранное.'})
        return data

    def create(self, validated_data):
        return FavoriteRecipe.objects.create(**validated_data)

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe, context=self.context).data
