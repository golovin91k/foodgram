import csv
import codecs

from django_filters.rest_framework import DjangoFilterBackend
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse
from djoser.conf import settings
from djoser.views import UserViewSet
from rest_framework import mixins, viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import (
    SpecialUserCreateSerializer, TagSerializer, SpecialUserSerializer,
    AvatarSerializer, IngredientSerializer, RecipeCreateSerializer,
    RecipeGetSerializer, SubscribeCreateSerializer, ShortRecipeSerializer,
    SetPasswordSerializer, SubscribeReturnSerializer, ShoppingCartCreateSerializer, FavoriteRecipeCreateSerializer)
from recipes.models import (
    Recipe, Ingredient, FavoriteRecipe, Tag, ShortLink,
    ShoppingCart, Subscription)
from .pagination import CustomPaginator
from .permissions import IsCurrentUserOrAdminOrReadOnly
from .filters import RecipeFilter
from .utils import sum_ingredients


User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = SpecialUserSerializer
    pagination_class = CustomPaginator

    def get_queryset(self):
        if self.action == 'list':
            return User.objects.all()
        return super().get_queryset()

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = settings.PERMISSIONS.me
        return super().get_permissions()

    @action(methods=['put', 'delete'], detail=False, url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def avatar(self, request):
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                data=request.data, instance=request.user)
            if serializer.is_valid():
                serializer.save(
                    validated_data=request.data, instance=request.user)
                return Response(serializer.data)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        request.user.avatar.delete()
        return Response(
            'Avatar is deleted', status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post', ], detail=False, url_path='set_password',
            permission_classes=[IsAuthenticated],
            serializer_class=[SetPasswordSerializer, ])
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data,)
        if serializer.is_valid():
            serializer.save(validated_data=request.data, instance=request.user)
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post', 'delete'], detail=True, url_path='subscribe',
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=kwargs['id'])
        if request.method == 'POST':
            serializer = SubscribeCreateSerializer(
                data={'author': author.id}, context={'request': request})
            serializer.is_valid(raise_exception=True)
            subscription = serializer.save(subscriber=request.user)
            return Response(SubscribeReturnSerializer(
                subscription.author,
                context={'request': request}).data,
                status=status.HTTP_201_CREATED)

        if not User.objects.filter(id=kwargs['id']).exists():
            return Response(
                {'errors': 'Такого автора не существует.'},
                status=status.HTTP_404_NOT_FOUND)
        try:
            obj = Subscription.objects.get(
                author=author, subscriber=request.user)
            obj.delete()
            return Response({'status': 'Автор удален из подписок'},
                            status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response({'status': 'Вы не подписаны на этого автора'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get', ], detail=False, url_path='subscriptions',
            permission_classes=[IsAuthenticated],
            pagination_class=CustomPaginator)
    def subscriptions(self, request):
        authors_id = self.request.user.sub_authors.all().values_list(
            'author', flat=True)
        authors_queryset = []
        for id in authors_id:
            authors_queryset.append(get_object_or_404(User, pk=id))
        paginate_user_subscriptions = self.paginate_queryset(authors_queryset)
        serializer = SubscribeReturnSerializer(
            paginate_user_subscriptions,
            context={'request': request},
            many=True)
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsCurrentUserOrAdminOrReadOnly]
    pagination_class = CustomPaginator
    http_method_names = [
        'get', 'post', 'patch',
        'delete', 'list', 'retrieve']
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):

        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeGetSerializer

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = FavoriteRecipeCreateSerializer(
                data={'recipe': pk}, context={'request': request})
            serializer.is_valid(raise_exception=True)
            favorite = serializer.save(user=request.user)
            favorite_data = ShortRecipeSerializer(
                favorite.recipe,
                context={'request': request}).data
            return Response(
                data=favorite_data,
                status=status.HTTP_201_CREATED)

        try:
            obj = FavoriteRecipe.objects.get(
                recipe=recipe, user=request.user)
            obj.delete()
            return Response({'status': 'Рецепт удален из избранного.'},
                            status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response({'status': 'Этого рецепта нет в избранном.'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = ShoppingCartCreateSerializer(
                data={'recipe': pk}, context={'request': request})
            serializer.is_valid(raise_exception=True)
            shopping_cart = serializer.save(user=request.user)
            shopping_cart_data = ShortRecipeSerializer(
                shopping_cart.recipe,
                context={'request': request}).data
            return Response(
                data=shopping_cart_data,
                status=status.HTTP_201_CREATED)

        try:
            obj = ShoppingCart.objects.get(
                recipe=recipe, user=request.user)
            obj.delete()
            return Response({'status': 'Рецепт удален из списка покупок.'},
                            status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response({'status': 'Этого рецепта нет в списке покупок.'},
                            status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['get', ],
            permission_classes=(IsAuthenticated, ))
    def download_shopping_cart(self, request):
        recipes_in_user_shopping_cart = ShoppingCart.objects.filter(
            user=self.request.user)
        ingredients_dict = sum_ingredients(recipes_in_user_shopping_cart)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = ('attachment;'
                                           'filename="exported_data.csv"')
        response.write(codecs.BOM_UTF8)
        writer = csv.writer(response)
        for ingredient in ingredients_dict.items():
            writer.writerow(ingredient)
        return response

    @action(detail=True, methods=['get', ],
            permission_classes=(AllowAny,), url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = Recipe.objects.get(id=pk)
        try:
            shortlink = ShortLink.objects.get(recipe=recipe)
            return Response({'short-link': request.META['HTTP_HOST']
                             + '/s/' + f'{shortlink.shortlink}'},)
        except ObjectDoesNotExist:
            return Response({'status': 'Такого рецепта не существует.'})


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    pagination_class = None
    http_method_names = ['get', 'list', 'retrieve']
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class IngredientViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    pagination_class = None
    http_method_names = ['get', 'list', 'retrieve']
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny, ]
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name', )


@ require_http_methods(["GET", ])
def shortlinkview(request, link):
    try:
        shortlink_obj = ShortLink.objects.get(shortlink=link)
        return redirect(f'/recipes/{shortlink_obj.recipe.id}')
    except ObjectDoesNotExist:
        return Response(
            {'status': 'Такой короткой ссылки на рецепт не существует'})
