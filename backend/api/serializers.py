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

User = get_user_model()

"""
Вспомогательный сериализатор указан ниже:
"""


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


"""
Сериализаторы для модели User указаны ниже.
"""


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ("email", "id", "username",
                  "first_name", "last_name", "password")
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
        }

    def validate_username(self, value):
        if re.match(r'^[\w.@+-]+\Z', value):
            return value
        else:
            raise serializers.ValidationError('Некорректное имя пользователя')


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed', 'avatar',)

    def get_is_subscribed(self, obj):
        current_user = self.context['request'].user
        if current_user.is_authenticated and current_user != obj:
            if Subscription.objects.filter(author=obj,
                                           subscriber=current_user):
                return True
            return False
        return False


class AvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField()

    def save(self, instance, validated_data):
        instance.avatar = self.validated_data['avatar']
        instance.save()
        return instance


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField()
    current_password = serializers.CharField()

    def save(self, instance, validated_data):
        if instance.check_password(validated_data['current_password']):
            instance.set_password(validated_data['new_password'])
            instance.save()
            return instance
        raise serializers.ValidationError({'Введен неверный текущий пароль'})


"""
Сериализаторы для остальных моделей указаны ниже.
"""


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeGetSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id")
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True)

    class Meta:
        model = IngredientInRecipe
        fields = ["id", "name", "measurement_unit", "amount"]


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeGetSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    image = Base64ImageField()
    author = CustomUserSerializer(read_only=True)
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
                ingr_obj = Ingredient.objects.get(id=obj['id'])
                if ingr_obj in ingr_list:
                    raise serializers.ValidationError(
                        'В рецепт нельзя добавлять одинаковые ингредиентов')
                ingr_list.append(ingr_obj)
            except ObjectDoesNotExist:
                raise serializers.ValidationError(
                    'Ингредиента с таким id нет.')
            if obj['amount'] < 1:
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
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше 1')
        return value

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        recipe.save()
        for ingr_obj in ingredients:
            obj = IngredientInRecipe.objects.create(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=ingr_obj['id']),
                amount=ingr_obj['amount'])
            obj.save
        create_shortlink(recipe)
        return recipe

    def update(self, instance, validated_data):
        list_obj = ['tags', 'ingredients']
        for obj in list_obj:
            if obj not in validated_data.keys():
                raise serializers.ValidationError
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        if not tags or not ingredients:
            raise serializers.ValidationError('sss')
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        instance.tags.set(tags)
        IngredientInRecipe.objects.filter(recipe=instance).delete()
        for ingredient_obj in ingredients:
            obj = IngredientInRecipe.objects.create(
                recipe=instance,
                ingredient=Ingredient.objects.get(
                    id=ingredient_obj['id']), amount=ingredient_obj['amount'])
            obj.save
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeGetSerializer(instance, context=self.context).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    image = Base64ImageField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class SubscriptionSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='author.email',)
    id = serializers.ReadOnlyField(source='author.id',)
    username = serializers.ReadOnlyField(source='author.username',)
    first_name = serializers.ReadOnlyField(source='author.first_name',)
    last_name = serializers.ReadOnlyField(source='author.last_name',)
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = Base64ImageField(source='author.avatar',)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'avatar',
                  'recipes_count')

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
        if recipes_limit:
            author_recipes = author_recipes[:int(recipes_limit)]
        return ShortRecipeSerializer(author_recipes,
                                     many=True, read_only=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()


class SubscribeSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'avatar',
                  'recipes_count')

    def validate(self, data):
        author = self.instance
        subscriber = self.context['request'].user
        if author == subscriber:
            raise serializers.ValidationError
        if Subscription.objects.filter(author=author,
                                       subscriber=subscriber).exists():
            raise ValidationError()
        return data

    def get_is_subscribed(self, obj):
        current_user = self.context['request'].user
        if current_user.is_authenticated and current_user != obj:
            if Subscription.objects.filter(author=obj,
                                           subscriber=current_user):
                return True
            return False
        return False

    def get_recipes(self, obj):
        author_recipes = Recipe.objects.filter(author=obj)
        request_recipes_limit = self.context.get('request').GET
        recipes_limit = request_recipes_limit.get('recipes_limit')
        if recipes_limit:
            author_recipes = author_recipes[:int(recipes_limit)]
        return ShortRecipeSerializer(author_recipes,
                                     many=True, read_only=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()
