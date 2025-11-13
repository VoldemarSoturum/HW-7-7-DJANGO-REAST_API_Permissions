from django.contrib import admin
from .models import Advertisement, Favorite

# Регистрируем модель Advertisement в админке «декоратором».
# Эквивалент admin.site.register(Advertisement, AdvertisementAdmin),
# но компактнее и читается лучше.
@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    # Какие поля показывать в списке объектов (таблица в админке).
    # Поля должны существовать в модели или быть свойствами/методами admin-класса.
    list_display = ('id', 'title', 'status', 'creator', 'created_at')

    # Панель фильтров справа: позволяет быстро сузить список по значениям полей.
    # Для FK (creator) Django отдаст выпадающий список пользователей,
    # для choices (status) — список доступных статусов.
    list_filter = ('status', 'creator')


# Аналогично регистрируем модель избранного.
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    # Какие колонки показывать в списке избранного:
    # id, пользователь, объявление, дата добавления.
    list_display = ('id', 'user', 'advertisement', 'created_at')

    # Фильтр по пользователю — удобно смотреть «чьи избранные».
    list_filter = ('user',)
