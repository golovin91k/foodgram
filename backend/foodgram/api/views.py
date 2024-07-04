import csv

from django_filters.rest_framework import DjangoFilterBackend
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from django.http import HttpResponse
from rest_framework import mixins, viewsets
from djoser.views import UserViewSet
from djoser.conf import settings
from rest_framework import mixins, viewsets, status, filters
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


from .serializers import (CustomUserCreateSerializer, TagSerializer,
                          CustomUserSerializer, AvatarSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeGetSerializer,
                          ShortRecipeSerializer, SetPasswordSerializer, SubscriptionSerializer)
from recipes.models import (Recipe, Ingredient, FavoriteRecipe, Tag, ShortLink,
                            ShoppingCart, IngredientInRecipe, Subscription)
from .pagination import CustomPaginator
from .permissions import IsOwnerOrReadOnly
from .filters import IngredientFilter, RecipeFilter


User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPaginator

    def get_permissions(self):
        if self.action == "me":
            self.permission_classes = settings.PERMISSIONS.me
        return super().get_permissions()

    def get_queryset(self):
        queryset = User.objects.all()
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        elif self.action == 'avatar':
            return AvatarSerializer
        elif self.action == 'set_password':
            return SetPasswordSerializer
        return CustomUserSerializer

    def perform_create(self, serializer, *args, **kwargs):
        serializer.save(*args, **kwargs)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['put', 'delete'], detail=False, url_path='me/avatar',
            permission_classes=[IsAuthenticated])
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
            return Response('Avatar is deleted', status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post',], detail=False, url_path='set_password',
            permission_classes=[IsAuthenticated],
            serializer_class=[SetPasswordSerializer,])
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data,)
        if serializer.is_valid():
            serializer.save(validated_data=request.data, instance=request.user)
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post', 'delete'], detail=True, url_path='subscribe',
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, **kwargs):
        if request.method == 'POST':
            author = User.objects.get(id=kwargs['id'])
            subscriber = User.objects.get(id=self.request.user.id)
            serializer = SubscriptionSerializer(
                author, data=request.data, context={"request": request})
            serializer.is_valid()
            print(request.data)
            Subscription.objects.get_or_create(
                author=author, subscriber=subscriber)
            # serializer = SubscriptionSerializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            author = User.objects.get(id=kwargs['id'])
            subscriber = User.objects.get(id=self.request.user.id)
            try:
                obj = Subscription.objects.get(
                    author=author, subscriber=subscriber)
                obj.delete()
                return Response({'status': 'Автор удален из подписок'})
            except ObjectDoesNotExist:
                return Response({'status': 'Вы не подписаны на этого автора'})

    @action(methods=['get',], detail=False, url_path='subscriptions',
            permission_classes=[IsAuthenticated], pagination_class=CustomPaginator)
    def subscriptions(self, request):
        user = self.request.user
        user_subscriptions = user.authors.all()
        authors = []
        for single_subscription in user_subscriptions:
            #print(single_subscription.author)
            authors.append(single_subscription.author)
        print(authors)
        serializer = SubscriptionSerializer(authors, data=request.data, context={
                                            "request": request}, many=True)
        serializer.is_valid()
        #print(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)
        # return Response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)
    pagination_class = CustomPaginator
    http_method_names = ['get', 'post', 'patch',
                         'delete', 'list', 'retrieve',]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):

        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeGetSerializer

    @action(detail=True, methods=['post', 'delete'], permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            serializer = ShortRecipeSerializer(data=request.data)
            if serializer.is_valid():
                recipe = Recipe.objects.get(id=pk)
                user = self.request.user
                FavoriteRecipe.objects.get_or_create(recipe=recipe, user=user)
                return Response({'status': 'Рецепт добавлен в избранное'})
        if request.method == 'DELETE':
            try:
                obj = FavoriteRecipe.objects.get(
                    recipe=pk, user=self.request.user)
                obj.delete()
                return Response({'status': 'Рецепт удален из избранного'})
            except ObjectDoesNotExist:
                return Response({'status': 'Этого рецепта нет в избранном'})

    @action(detail=True, methods=['post', 'delete'], permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            serializer = ShortRecipeSerializer(data=request.data)
            if serializer.is_valid():
                recipe = Recipe.objects.get(id=pk)
                ShoppingCart.objects.get_or_create(
                    recipe=recipe, user=self.request.user)
                return Response({'status': 'Рецепт добавлен в список покупок'})
        if request.method == 'DELETE':
            try:
                obj = ShoppingCart.objects.get(
                    recipe=pk, user=self.request.user)
                obj.delete()
                return Response({'status': 'Рецепт удален из списка покупок'})
            except ObjectDoesNotExist:
                return Response({'status': 'Этого рецепта нет в списке покупок'})

    @action(detail=False, methods=['get',])
    def download_shopping_cart(self, request,):
        recipes_in_user_shopping_cart = ShoppingCart.objects.filter(
            user=self.request.user)
        shopping_cart = {}
        for single_recipe in recipes_in_user_shopping_cart:
            ingredients_in_single_recipe = single_recipe.recipe.ingredients.all()
            for single_ingredient in ingredients_in_single_recipe:
                ingredientinrecipe_obj = IngredientInRecipe.objects.get(
                    recipe=single_recipe.recipe, ingredient=single_ingredient)
                print(single_ingredient.name)
                if (single_ingredient.name + ', ' + single_ingredient.measurement_unit) in shopping_cart.keys():
                    shopping_cart[single_ingredient.name + ', '
                                  + single_ingredient.measurement_unit] += ingredientinrecipe_obj.amount
                else:
                    shopping_cart[single_ingredient.name + ', '
                                  + single_ingredient.measurement_unit] = ingredientinrecipe_obj.amount
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="export.csv"'
        writer = csv.writer(response)
        for ingredient in shopping_cart.items():
            writer.writerow(ingredient)
            return Response({'status': 'Этого рецепта нет в списке покупок'})

    @action(detail=True, methods=['get',], permission_classes=(AllowAny,), url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = Recipe.objects.get(id=pk)
        try:
            shortlink = ShortLink.objects.get(recipe=recipe)
            return Response({'short-link': f'{shortlink.shortlink}'})
        except ObjectDoesNotExist:
            return Response({'status': 'Этого рецепта нет в списке покупок'})


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    pagination_class = None
    http_method_names = ['get', 'list', 'retrieve',]
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class IngredientViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):

    queryset = Ingredient.objects.all()
    pagination_class = None
    http_method_names = ['get', 'list', 'retrieve',]
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny,]
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name', )


@require_http_methods(["GET",])
def shortlinkview(request, link):
    shortlink_obj = ShortLink.objects.get(shortlink=link)
    return redirect(f'/api/recipes/{shortlink_obj.recipe.id}')
