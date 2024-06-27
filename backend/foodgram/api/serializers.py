import base64

from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from django.db import transaction
from recipes.models import Recipe, Tag, Ingredient, IngredientInRecipe

User = get_user_model()


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


class CustomUserSerializer(UserSerializer):
    # is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'avatar',)  # 'is_subscribed')


class AvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField()

    def save(self, instance, validated_data):
        instance.avatar = self.validated_data['avatar']
        instance.save()
        return instance


"""
Сериализаторы для остальных моделей указаны ниже.
"""


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeGetSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.CharField(source="ingredients.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredients.measurement_unit", read_only=True)
    
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
    ingredients_set = IngredientInRecipeGetSerializer(many=True,)

    class Meta:
        model = Recipe
        fields = ('ingredients_set', 'author', 'image', 'tags')


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

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        recipe.save()
        for ingredient_1 in ingredients:
            obj = IngredientInRecipe.objects.create(recipe=recipe,
                                                    ingredient=Ingredient.objects.get(
                                                        id=ingredient_1['id']),
                                                    amount=ingredient_1['amount'])
            obj.save
        print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', recipe.ingredients.all())
        return recipe


    def to_representation(self, instance):
        return RecipeGetSerializer(instance, context=self.context).data

