import base64
import re

from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import (Recipe, Tag, Ingredient, IngredientInRecipe,
                            FavoriteRecipe, Subscription, ShoppingCart,)
from .utils import create_shortlink
from .constans import MINIMUM_AMOUNT, MINIMUM_COOKING_TIME


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
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'password')
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
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        current_user = self.context['request'].user
        return (current_user.is_authenticated and current_user != obj
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
    id = serializers.IntegerField(source='ingredient.id')
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                {'Ингредиента с таким id не существует.'})
        return value

    def validate_amount(self, value):
        if value < MINIMUM_AMOUNT:
            raise serializers.ValidationError(
                {'Введено неверное количество ингредиента: '
                 'количество ингредиента не может быть меньше единицы.'})
        return value


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
        fields = ('id', 'tags',
                  'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image',
                  'text', 'cooking_time')

    def get_is_favorited(self, obj):
        current_user = self.context['request'].user
        if current_user.is_authenticated:
            if FavoriteRecipe.objects.filter(user=current_user, recipe=obj):
                return True
            else:
                return False
        return False

    def get_is_in_shopping_cart(self, obj):
        current_user = self.context['request'].user
        if current_user.is_authenticated:
            if ShoppingCart.objects.filter(user=current_user, recipe=obj):
                return True
            else:
                return False
        return False


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания и изменения рецепта."""
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    image = Base64ImageField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    ingredients = IngredientInRecipeCreateSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'name', 'image',
                  'text', 'cooking_time', 'ingredients')

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы один ингредиент.'
            )
        ingr_list = []
        for obj in value:
            try:
                ingr_obj = Ingredient.objects.get(id=obj['ingredient']['id'])
                if ingr_obj in ingr_list:
                    raise serializers.ValidationError(
                        'В рецепт нельзя добавлять одинаковые ингредиенты')
                ingr_list.append(ingr_obj)
            except ObjectDoesNotExist:
                raise serializers.ValidationError(
                    'Ингредиента с таким id нет.')
            if obj['amount'] < MINIMUM_AMOUNT:
                raise serializers.ValidationError(
                    'Количество ингредиента не должно быть меньше 1.')
        return value

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

    def validate_cooking_time(self, value):
        if value < MINIMUM_COOKING_TIME:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше 0')
        return value

    def create_ingredients_for_recipe(self, recipe, ingredients):
        ingredients_list = []
        for ingredient in ingredients:
            ingredients_list.append(IngredientInRecipe(
                recipe=recipe,
                ingredient=Ingredient.objects.get(
                    id=ingredient['ingredient']['id']),
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
        if not tags or not ingredients:
            raise serializers.ValidationError(
                {'Отсутствуют тег или ингредиент.'})
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

    def get_recipes(self, obj):
        author_recipes = Recipe.objects.filter(author=obj.author)
        request_recipes_limit = self.context.get('request').GET
        recipes_limit = request_recipes_limit.get('recipes_limit')
        try:
            if int(recipes_limit):
                author_recipes = author_recipes[:int(recipes_limit)]
                return ShortRecipeSerializer(author_recipes,
                                             many=True, read_only=True).data
        except ValueError:
            raise ValueError('Значение recipes_limit должно быть числом.')

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()


class SubscribeReturnSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения объекта пользователя после
    создания подписки на этого пользователя.
    """
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        current_user = self.context['request'].user
        if current_user.is_authenticated and current_user != obj.author:
            if Subscription.objects.filter(author=obj.author,
                                           subscriber=current_user):
                return True
            return False
        return False

    def get_recipes(self, obj):
        author_recipes = Recipe.objects.filter(author=obj.author)
        request_recipes_limit = self.context.get('request').GET
        recipes_limit = request_recipes_limit.get('recipes_limit')
        try:
            if recipes_limit is not None and isinstance(recipes_limit, int):
                author_recipes = author_recipes[:int(recipes_limit)]
                return ShortRecipeSerializer(author_recipes,
                                             many=True, read_only=True).data
        except ValueError:
            raise ValueError('Значение recipes_limit должно быть числом.')
        return ShortRecipeSerializer(author_recipes,
                                     many=True, read_only=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()


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
        if Subscription.objects.filter(author=author,
                                       subscriber=subscriber).exists():
            raise ValidationError({'Вы уже подписаны на этого пользователя'})
        return data

    def create(self, validated_data):
        return Subscription.objects.create(**validated_data)
