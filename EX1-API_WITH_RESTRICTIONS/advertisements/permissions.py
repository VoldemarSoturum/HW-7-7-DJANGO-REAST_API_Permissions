from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrAdmin(BasePermission):
    """
    Объектное разрешение для DRF.

    Идея:
    - Любые безопасные методы (чтение) разрешены всем.
      DRF считает безопасными методы из SAFE_METHODS: ('GET', 'HEAD', 'OPTIONS').
    - Небезопасные методы (создание/изменение/удаление) разрешены только:
        * аутентифицированному владельцу объекта, или
        * администратору (user.is_staff == True).

    Использование:
        class SomeViewSet(ModelViewSet):
            permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]
    """

    def has_object_permission(self, request, view, obj):
        """
        Метод объектного уровня. DRF автоматически вызывает его,
        когда у операции есть конкретный объект (detail view).
        Для list-эндпоинта (списка) объектных проверок нет — там применяется has_permission.

        Аргументы:
        - request: текущий запрос (содержит request.user, request.method и т.д.)
        - view: текущий view/viewset (на случай, если нужна логика по action)
        - obj: сам объект модели, к которому пытаются получить доступ
        """

        # 1) Чтение всегда разрешено (GET, HEAD, OPTIONS)
        if request.method in SAFE_METHODS:
            return True

        # 2) Нужен аутентифицированный пользователь
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # 3) Админ (is_staff) может всё
        if getattr(user, 'is_staff', False):
            return True

        # 4) Иначе разрешаем только владельцу объекта
        # Предполагается, что у модели есть ForeignKey на User с именем 'creator'
        # и Django автоматически добавляет поле 'creator_id' (целочисленный FK).
        # Сравнение по ID удобно и не требует доп. запросов.
        return getattr(obj, 'creator_id', None) == user.id
