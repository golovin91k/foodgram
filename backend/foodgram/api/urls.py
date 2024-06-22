from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet # CustomUserListViewSet


router = DefaultRouter()
#router.register('users', CustomUserListViewSet)
router.register('users', CustomUserViewSet)


urlpatterns = [
   # path('auth/', CustomAuthToken.as_view()),
   # path('auth/', include('djoser.urls')),
   # path('auth/', include('djoser.urls.jwt')),
    path('', include('djoser.urls.authtoken')),
    path('', include(router.urls)),

]
