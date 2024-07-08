from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CustomUserViewSet, RecipeViewSet,
                    TagViewSet, IngredientViewSet)


router = DefaultRouter()

router.register('users', CustomUserViewSet)
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path(r'auth/', include('djoser.urls')),
    path(r'auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
