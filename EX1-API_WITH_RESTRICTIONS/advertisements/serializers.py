from django.contrib.auth.models import User
from rest_framework import serializers

from advertisements.models import Advertisement, Favorite


class UserSerializer(serializers.ModelSerializer):
    """Serializer для пользователя."""
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name")


class AdvertisementSerializer(serializers.ModelSerializer):
    """Serializer для объявления с флагом 'is_favorited' и поддержкой статуса DRAFT."""
    creator = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Advertisement
        fields = (
            "id",
            "title",
            "description",
            "creator",
            "status",
            "created_at",
            "updated_at",    # покажем время обновления
            "is_favorited",  # находится ли объявление в избранном у текущего пользователя
        )
        read_only_fields = ("creator", "created_at", "updated_at")

    def get_is_favorited(self, obj):
        """Вернёт True, если текущее объявление в избранном у request.user."""
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return Favorite.objects.filter(user=user, advertisement=obj).exists()

    def create(self, validated_data):
        """Текущий пользователь — создатель объявления (переопределять через API нельзя)."""
        validated_data["creator"] = self.context["request"].user
        return super().create(validated_data)

    def validate(self, data):
        """
        Бизнес-правило: у одного пользователя не может быть более 10 объявлений в статусе OPEN.
        Проверяем при создании и обновлении (включая перевод в OPEN).
        """
        # Безопасно получаем константу OPEN (с TextChoices или строкой по умолчанию)
        try:
            OPEN = Advertisement.Status.OPEN
        except Exception:
            OPEN = "OPEN"

        # Определяем целевой статус после операции
        if self.instance is None:
            # Создание: если статус не передан — в модели стоит default=OPEN
            target_status = data.get("status", OPEN)
            user_for_limit = self.context["request"].user
            exclude_id = None
        else:
            # Обновление: берём новый статус, если он передан, иначе текущий
            target_status = data.get("status", self.instance.status)
            # Лимит относится к владельцу объявления, даже если апдейт делает админ
            user_for_limit = getattr(self.instance, "creator", None) or self.context["request"].user
            exclude_id = self.instance.id

        # Нужна ли проверка лимита (только когда целевой статус = OPEN)
        def is_open(value):
            try:
                return value == Advertisement.Status.OPEN
            except Exception:
                return str(value).upper() == "OPEN"

        if is_open(target_status):
            qs = Advertisement.objects.filter(creator=user_for_limit, status=OPEN)
            if exclude_id:
                qs = qs.exclude(id=exclude_id)
            if qs.count() >= 10:
                raise serializers.ValidationError(
                    {"status": "Превышен лимит: не более 10 открытых объявлений на пользователя."}
                )

        return data
