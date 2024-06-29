import csv

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from rest_framework import mixins, viewsets
from djoser.views import UserViewSet
from djoser.conf import settings
from rest_framework import mixins, viewsets
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


from .serializers import (CustomUserCreateSerializer,
                          CustomUserSerializer, RecipeCreateSerializer,
                          RecipeGetSerializer, FavoriteRecipeSerializer)
from recipes.models import Recipe, Ingredient, FavoriteRecipe, ShoppingCart, IngredientInRecipe


User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = PageNumberPagination

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = settings.PERMISSIONS.user_create
        elif self.action == "activation":
            self.permission_classes = settings.PERMISSIONS.activation
        elif self.action == "resend_activation":
            self.permission_classes = settings.PERMISSIONS.password_reset
        elif self.action == "list":
            self.permission_classes = settings.PERMISSIONS.user_list
        elif self.action == "reset_password":
            self.permission_classes = settings.PERMISSIONS.password_reset
        elif self.action == "reset_password_confirm":
            self.permission_classes = settings.PERMISSIONS.password_reset_confirm
        elif self.action == "set_password":
            self.permission_classes = settings.PERMISSIONS.set_password
        elif self.action == "set_username":
            self.permission_classes = settings.PERMISSIONS.set_username
        elif self.action == "reset_username":
            self.permission_classes = settings.PERMISSIONS.username_reset
        elif self.action == "reset_username_confirm":
            self.permission_classes = settings.PERMISSIONS.username_reset_confirm
        elif self.action == "me":
            self.permission_classes = settings.PERMISSIONS.user_delete
        elif self.action == "destroy" or (
            self.action == "me" and self.request and self.request.method == "DELETE"
        ):
            self.permission_classes = settings.PERMISSIONS.user_delete
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.all()
        return queryset

    def get_serializer_class(self):
        print(self.action)
        if self.action in ('create',):
            return CustomUserCreateSerializer
        if self.action == 'avatar':
            return AvatarSerializer
        # if self.action == 'set_password':
            # return SetPasswordSerializer
        return CustomUserSerializer

    @action(methods=['put', 'delete'], detail=False, url_path='avatar')
    def avatar(self, request):
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                data=request.data, instance=request.user)
            if serializer.is_valid():
                serializer.save(validated_data=request.data,
                                instance=request.user)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            request.user.avatar.delete()
            return Response('Avatar is deleted')


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [AllowAny,]
    http_method_names = ['get', 'post', 'patch',
                         'delete', 'list', 'retrieve',]

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeGetSerializer

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            serializer = FavoriteRecipeSerializer(data=request.data)
            if serializer.is_valid():
                recipe = Recipe.objects.get(id=pk)
                user = self.request.user
                FavoriteRecipe.objects.get_or_create(recipe=recipe, user=user)
                return Response({'status': 'Рецепт добавлен в избранное'})
        if request.method == 'DELETE':
            try:
                obj = FavoriteRecipe.objects.get(recipe=pk, user=self.request.user)
                obj.delete()
                return Response({'status': 'Рецепт удален из избранного'})
            except ObjectDoesNotExist:
                return Response({'status': 'Этого рецепта нет в избранном'})

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            serializer = FavoriteRecipeSerializer(data=request.data)
            if serializer.is_valid():
                recipe = Recipe.objects.get(id=pk)
                ShoppingCart.objects.get_or_create(recipe=recipe, user=self.request.user)
                """
     
                """
                return Response({'status': 'Рецепт добавлен в список покупок'})
        if request.method == 'DELETE':
            try:
                obj = ShoppingCart.objects.get(recipe=pk, user=self.request.user)
                obj.delete()
                return Response({'status': 'Рецепт удален из списка покупок'})
            except ObjectDoesNotExist:
                return Response({'status': 'Этого рецепта нет в списке покупок'})

    @action(detail=False, methods=['get',])
    def download_shopping_cart(self, request,):
        recipes_in_user_shopping_cart = ShoppingCart.objects.filter(user=self.request.user)
        shopping_cart = {}
        for single_recipe in recipes_in_user_shopping_cart:
            ingredients_in_single_recipe = single_recipe.recipe.ingredients.all()
            for single_ingredient in ingredients_in_single_recipe:
                ingredientinrecipe_obj = IngredientInRecipe.objects.get(recipe=single_recipe.recipe, ingredient=single_ingredient)
                print(single_ingredient.name)
                if (single_ingredient.name + ', ' + single_ingredient.measurement_unit) in shopping_cart.keys():
                    shopping_cart[single_ingredient.name + ', ' + single_ingredient.measurement_unit] += ingredientinrecipe_obj.amount
                else:
                    shopping_cart[single_ingredient.name + ', ' + single_ingredient.measurement_unit] = ingredientinrecipe_obj.amount
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="export.csv"'
        writer = csv.writer(response)
        for ingredient in shopping_cart.items():
            writer.writerow(ingredient)
        return response
