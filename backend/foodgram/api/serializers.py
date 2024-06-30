import base64

from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import Recipe, Tag, Ingredient, IngredientInRecipe, FavoriteRecipe, Subscription


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
   # id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
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

    class Meta:
        model = Recipe
        fields = '__all__'


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
        for ingredient_obj in ingredients:
            obj = IngredientInRecipe.objects.create(recipe=recipe,
                                                    ingredient=Ingredient.objects.get(
                                                        id=ingredient_obj['id']),
                                                    amount=ingredient_obj['amount'])
            obj.save
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        instance.tags.set(tags)
        for ingredient_obj in ingredients:
            obj = IngredientInRecipe.objects.create(recipe=instance, ingredient=Ingredient.objects.get(
                id=ingredient_obj['id']), amount=ingredient_obj['amount'])
            obj.save
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeGetSerializer(instance, context=self.context).data


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    image = serializers.CharField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes = FavoriteRecipeSerializer(many=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'avatar', 'recipes', 'recipes_count')

    def get_recipes_count(self, obj):
        return len(obj.recipes.all())
