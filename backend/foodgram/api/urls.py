from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet, RecipeViewSet


router = DefaultRouter()
#router.register('users/avatar/', AvatarViewSet)
router.register('users', CustomUserViewSet)
router.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path(r'auth/', include('djoser.urls')),
    path(r'auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
