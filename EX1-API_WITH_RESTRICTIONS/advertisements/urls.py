from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import AdvertisementViewSet

router = SimpleRouter()
router.register('advertisements', AdvertisementViewSet, basename='advertisement')

urlpatterns = [
    path('', include(router.urls)),
]
