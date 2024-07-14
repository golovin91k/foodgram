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

from .serializers import (SpecialUserCreateSerializer, TagSerializer,
                          SpecialUserSerializer, AvatarSerializer,
                          IngredientSerializer, RecipeCreateSerializer,
                          RecipeGetSerializer, SubscribeSerializer,
                          ShortRecipeSerializer, SetPasswordSerializer,
                          SubscriptionSerializer)
from recipes.models import (Recipe, Ingredient, FavoriteRecipe, Tag, ShortLink,
                            ShoppingCart, Subscription)
from .pagination import CustomPaginator
from .permissions import IsOwnerOrReadOnly
from .filters import RecipeFilter
from .utils import sum_ingredients


User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = SpecialUserSerializer
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
            return SpecialUserCreateSerializer
        elif self.action == 'avatar':
            return AvatarSerializer
        elif self.action == 'set_password':
            return SetPasswordSerializer
        return SpecialUserSerializer

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
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            request.user.avatar.delete()
            return Response('Avatar is deleted',
                            status=status.HTTP_204_NO_CONTENT)

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
        if request.method == 'POST':
            author = get_object_or_404(User, id=kwargs['id'])
            subscriber = get_object_or_404(User, id=self.request.user.id)
            serializer = SubscribeSerializer(
                author, data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            Subscription.objects.get_or_create(author=author,
                                               subscriber=subscriber)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not User.objects.filter(id=kwargs['id']).exists():
                return Response({'errors': 'Такого автора не существует.'},
                                status=status.HTTP_404_NOT_FOUND)
            author = User.objects.get(id=kwargs['id'])
            subscriber = User.objects.get(id=self.request.user.id)
            try:
                obj = Subscription.objects.get(
                    author=author, subscriber=subscriber)
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
        user = self.request.user
        user_subscriptions = Subscription.objects.filter(subscriber=user)
        paginate_user_subscriptions = self.paginate_queryset(
            user_subscriptions)
        serializer = SubscriptionSerializer(paginate_user_subscriptions,
                                            context={'request': request},
                                            many=True)
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerOrReadOnly, IsAuthenticated)
    pagination_class = CustomPaginator
    http_method_names = ['get', 'post', 'patch',
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
        if request.method == 'POST':
            user = self.request.user
            if not Recipe.objects.filter(id=pk).exists():
                return Response({'errors': 'Такого рецепта не существует.'},
                                status=status.HTTP_404_NOT_FOUND)
            recipe = Recipe.objects.get(id=pk)
            if FavoriteRecipe.objects.filter(user=user,
                                             recipe=recipe).exists():
                return Response({'errors': ('Этот рецепт уже добавлен'
                                            'в список избранного')},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = ShortRecipeSerializer(recipe)
            FavoriteRecipe.objects.create(recipe=recipe, user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not Recipe.objects.filter(id=pk).exists():
                return Response({'errors': 'Такого рецепта не существует.'},
                                status=status.HTTP_404_NOT_FOUND)
            try:
                obj = FavoriteRecipe.objects.get(
                    recipe=pk, user=self.request.user)
                obj.delete()
                return Response({'status': 'Рецепт удален из избранного'},
                                status=status.HTTP_204_NO_CONTENT)
            except ObjectDoesNotExist:
                return Response({'status': 'Этого рецепта нет в избранном'},
                                status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            user = self.request.user
            if not Recipe.objects.filter(id=pk).exists():
                return Response({'errors': 'Такого рецепта не существует.'},
                                status=status.HTTP_404_NOT_FOUND)
            recipe = Recipe.objects.get(id=pk)
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response({'errors': ('Этот рецепт уже добавлен'
                                            'в список покупок')},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = ShortRecipeSerializer(recipe)
            ShoppingCart.objects.get_or_create(recipe=recipe,
                                               user=self.request.user)
            print(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not Recipe.objects.filter(id=pk).exists():
                return Response({'errors': 'Такого рецепта не существует.'},
                                status=status.HTTP_404_NOT_FOUND)
            try:
                obj = ShoppingCart.objects.get(
                    recipe=pk, user=self.request.user)
                obj.delete()
                return Response({'status': 'Рецепт удален из списка покупок'},
                                status=status.HTTP_204_NO_CONTENT)
            except ObjectDoesNotExist:
                return Response({'status': ('Этого рецепта нет'
                                            'в списке покупок')},
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
    shortlink_obj = ShortLink.objects.get(shortlink=link)
    return redirect(f'/recipes/{shortlink_obj.recipe.id}')
