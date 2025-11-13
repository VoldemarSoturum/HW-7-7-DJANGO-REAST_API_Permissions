from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend

from advertisements.serializers import AdvertisementSerializer
from advertisements.permissions import IsOwnerOrAdmin
from advertisements.filters import AdvertisementFilter
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from advertisements.models import Advertisement, Favorite

class AdvertisementViewSet(ModelViewSet):
    """ViewSet для объявлений."""

    # TODO: настройте ViewSet, укажите атрибуты для кверисета,
    #   сериализаторов и фильтров
    """ViewSet для объявлений."""

    """ViewSet для объявлений с поддержкой избранного и статуса DRAFT."""
    queryset = Advertisement.objects.all().select_related('creator')
    serializer_class = AdvertisementSerializer

    # фильтрация через django-filter
    filter_backends = [DjangoFilterBackend]
    filterset_class = AdvertisementFilter

    # базовый объектный пермишен: владелец/админ может менять; читать — всем
    permission_classes = [IsOwnerOrAdmin]

    def get_permissions(self):
        """
        Права доступа по action:
        - create/update/partial_update/destroy — только аутентифицированным + проверка владельца/админа
        - favorite/unfavorite/favorites — только аутентифицированным (любые объявления можно добавлять/убирать из избранного)
        - list/retrieve — доступны всем (объектный пермишен пропустит SAFE_METHODS)
        """
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        if self.action in ["favorite", "unfavorite", "favorites"]:
            return [IsAuthenticated()]
        return [IsOwnerOrAdmin()]

    def get_queryset(self):
        """
        Скрываем DRAFT от всех, кроме автора и админа:
        - админ (is_staff) видит всё
        - автор видит свои DRAFT
        - остальные DRAFT не видят
        """
        qs = super().get_queryset()
        user = self.request.user

        # админ видит всё, включая DRAFT
        if user.is_authenticated and user.is_staff:
            return qs

        # не админ, смертный обычный:
        if user.is_authenticated:
            return qs.filter(~Q(status=Advertisement.Status.DRAFT) | Q(creator=user))
        return qs.filter(~Q(status=Advertisement.Status.DRAFT))

    # ---------- Избранное ----------

    @action(detail=True, methods=["post"])
    def favorite(self, request, pk=None):
        """
        Добавить объявление в избранное текущего пользователя.
        Автор НЕ может добавить своё объявление в избранное.
        """
        ad = self.get_object()  # для этой action пермишены: только IsAuthenticated
        if ad.creator_id == request.user.id:
            return Response(
                {"detail": "Нельзя добавить в избранное своё объявление."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        fav, created = Favorite.objects.get_or_create(user=request.user, advertisement=ad)
        return Response(
            {"detail": "Добавлено в избранное."},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["delete"])
    def unfavorite(self, request, pk=None):
        """Удалить объявление из избранного текущего пользователя."""
        ad = self.get_object()
        Favorite.objects.filter(user=request.user, advertisement=ad).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def favorites(self, request):
        """
        Список объявлений, добавленных в избранное текущим пользователем.
        Возвращает те же поля, что и основной список (с пагинацией).
        """
        ads = Advertisement.objects.filter(favorites__user=request.user).select_related("creator")
        page = self.paginate_queryset(ads)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(ads, many=True)
        return Response(ser.data)