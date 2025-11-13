from django.conf import settings
from django.db import models

class Advertisement(models.Model):
    # Вложенный перечислимый тип (enum) для статуса.
    # TextChoices задаёт пару (machine value, human-readable label).
    # Значение хранится в БД как строка ('OPEN' / 'CLOSED' / 'DRAFT'),
    # а в админке/сериализаторе можно показать человекочитаемый ярлык.
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'      # опубликовано, видно всем
        CLOSED = 'CLOSED', 'Closed'  # закрыто, архив
        DRAFT = 'DRAFT', 'Draft'   # черновик — виден только автору и админу

    # Заголовок объявления. Обязательное строковое поле до 200 символов.
    title = models.CharField(max_length=200)

    # Текстовое описание произвольной длины. blank=True — можно оставить пустым
    # на уровне валидации Django (в БД по умолчанию хранится как NOT NULL с пустой строкой).
    description = models.TextField(blank=True)

    # Статус объявления. Ограничен набором choices из Status.
    # max_length=10 с запасом хватает под 'CLOSED' и 'DRAFT'.
    # default=Status.OPEN — новые объекты по умолчанию будут открыты.
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)

    # Автор объявления. ForeignKey к пользовательской модели.
    # settings.AUTH_USER_MODEL — корректно работает даже если User кастомный.
    # on_delete=models.CASCADE — если удалить пользователя, удалятся его объявления.
    # related_name='advertisements' — обратная связь: user.advertisements.all()
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='advertisements',
    )

    # Дата создания: заполняется один раз при insert.
    created_at = models.DateTimeField(auto_now_add=True)

    # Дата обновления: перезаписывается при каждом save() объекта.
    updated_at = models.DateTimeField(auto_now=True)


class Favorite(models.Model):
    # Пользователь, который добавил в избранное.
    # При удалении пользователя все его избранные записи удаляются (CASCADE).
    # related_name='favorite_ads' — обратная связь: user.favorite_ads.all() -> queryset Favorite
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_ads',
    )

    # Объявление, добавленное в избранное.
    # При удалении объявления соответствующие избранные записи тоже удаляются (CASCADE).
    # related_name='favorites' — обратная связь: ad.favorites.all() -> queryset Favorite
    advertisement = models.ForeignKey(
        Advertisement,
        on_delete=models.CASCADE,
        related_name='favorites',
    )

    # Когда добавили в избранное. Ставит timestamp при insert.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Уникальный составной ключ (user, advertisement).
        # Гарантирует на уровне БД, что один и тот же пользователь
        # не сможет добавить ОДНО объявление в избранное дважды.
        # Под капотом в PostgreSQL это ещё и уникальный индекс — ускоряет выборки.
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'advertisement'],
                name='uniq_favorite_user_ad',
            )
        ]

    def __str__(self):
        # Удобное представление объекта в админке/консоли.
        # self.advertisement_id — это "сырое" значение FK (целое, без запроса к БД).
        return f'{self.user} -> {self.advertisement_id}'
