import django_filters
from django_filters import rest_framework as filters

from advertisements.models import Advertisement


class AdvertisementFilter(filters.FilterSet):
    """Фильтры для объявлений."""
    created_at = django_filters.DateTimeFromToRangeFilter(field_name='created_at')
    creator = django_filters.NumberFilter(field_name='creator__id')
    status = django_filters.CharFilter(field_name='status')
    favorite = django_filters.BooleanFilter(method='filter_favorite')  # <-- NEW

    # TODO: задайте требуемые фильтры
    class Meta:
        model = Advertisement
        fields = ['creator', 'status', 'created_at', 'favorite']

    def filter_favorite(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if value and user and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset