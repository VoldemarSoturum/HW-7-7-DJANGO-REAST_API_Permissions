# API with Restrictions (DRF): Фильтрация, Валидация, Аутентификация, Троттлинг + Избранное и DRAFT

Учебный проект по Django REST Framework. Реализовано:
- Аутентификация по токену (DRF authtoken).
- Права: читать — всем; **менять/удалять** — **владелец** или **админ** (is_staff).
- Фильтрация по автору, статусу (`OPEN/CLOSED/DRAFT`), интервалам даты.
- Валидация: не более **10** объявлений в статусе **OPEN** на пользователя.
- Троттлинг: **для неавторизованных пользователей 10/мин**, **для авторизованных пользователей 20/мин**.
- **Дополнительно**: избранные объявления (favorite/unfavorite/favorites, фильтр `?favorite=true`).
- **Дополнительно**: статус **DRAFT** — виден только автору и админу.

---

## Установка и запуск (кратко)
1. Создай и активируй venv, установи зависимости:
   ```bash
   python -m venv .venv && . .venv/Scripts/activate  # (Windows PowerShell: .venv\Scripts\Activate.ps1)
   pip install -r requirements.txt
   # если файла нет: pip install django djangorestframework django-filter django-extensions pyOpenSSL werkzeug psycopg2-binary
   ```
2. Применить миграции и создать суперпользователя:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```
3. Запуск по HTTPS (локально):
   ```bash
   python manage.py runserver_plus --cert-file cert.pem 0.0.0.0:8000
   ```
   В VS Code включи **Rest Client: Ignore SSL Error** (`true`). Открывай `https://127.0.0.1:8000`.

**ALLOWED_HOSTS** в `settings.py`:
```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
```

**PostgreSQL (пример)**:
```python
DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': 'netology_app_advertisements',
    'USER': 'netology_advertisements',
    'PASSWORD': 'netology_advertisements',
    'HOST': '127.0.0.1',
    'PORT': '5432',
  }
}
```

---

## DRF настройки (важное)
```python
INSTALLED_APPS = [
  # ...
  'rest_framework',
  'rest_framework.authtoken',
  'django_filters',
  'django_extensions',   # для HTTPS dev
  'advertisements',
]

REST_FRAMEWORK = {
  'DEFAULT_AUTHENTICATION_CLASSES': [
    'rest_framework.authentication.TokenAuthentication',
    'rest_framework.authentication.SessionAuthentication',
  ],
  'DEFAULT_PERMISSION_CLASSES': [
    'rest_framework.permissions.IsAuthenticatedOrReadOnly',
  ],
  'DEFAULT_FILTER_BACKENDS': [
    'django_filters.rest_framework.DjangoFilterBackend',
  ],
  'DEFAULT_THROTTLE_CLASSES': [
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle',
  ],
  'DEFAULT_THROTTLE_RATES': {
    'anon': '10/min',
    'user': '20/min',
  },
}
```

`urls.py`:
```python
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
  path('api-token-auth/', obtain_auth_token),
  path('api/', include(router.urls)),
  path('admin/', admin.site.urls),
]
```

---

## REST Client: коллекция запросов

> Перед запуском обнови токены и id в блоке переменных.  
> Следи за порядком: блок **F** выполняй **до** удаления в **C4**, или используй другой id.

<details>
<summary>Развернуть .http</summary>

```http
@host = https://127.0.0.1:8000
@baseUrl = {{host}}/api

# ==== Ручные переменные ====
# Токен владельца объявлений user1
@token1 = 0cb79c9c6b2a09ab1f70e47decc86690247f7d5b
# Токен другого пользователя user2
@token2 = c0ae99b612b6d0ae1b66300f4d46a18e387308c8

# Числовые ID пользователей (creator.id)
@creator_id_user1 = 8
@creator_id_user2 = 2

# Числовые ID объявлений (pk) — укажи реальные ID из БД/ответов
# ad_id_user1 — объявление, созданное user1
@ad_id_user1 = 1
# ad_id_user2 — объявление, созданное user2
@ad_id_user2 = 2

# ==== Подготовка ====
# 1) Сервер в HTTPS:
#    python manage.py runserver_plus --cert-file cert.pem 0.0.0.0:8000
# 2) VS Code → Settings: "rest-client.ignoreSSL": true

###
# Получить токен по логину/паролю — возьми из ответа и вставь в @token1
POST {{host}}/api-token-auth/
Content-Type: application/json

{
  "username": "admin",
  "password": "admin"
}

###
# Получить токен по логину/паролю — возьми из ответа и вставь в @token2
POST {{host}}/api-token-auth/
Content-Type: application/json

{
  "username": "alice",
  "password": "alicePrincess"
}

# =====================================
#    БЛОК A: Создание и базовая проверка
# =====================================

###
# A1. Список объявлений (анонимно)
GET {{baseUrl}}/advertisements/
Content-Type: application/json

###
# A2. Создать объявление от user1 (OPEN)
#  — после создания возьми id из ответа и запиши в @ad_id_user1 сверху
POST {{baseUrl}}/advertisements/
Content-Type: application/json
Authorization: Token {{token1}}

{
  "title": "Стол из дуба (user1)",
  "description": "Продам стол, состояние отличное",
  "status": "OPEN"
}

###
# A3. Создать объявление от user2 (OPEN)
#  — после создания возьми id из ответа и запиши в @ad_id_user2 сверху
POST {{baseUrl}}/advertisements/
Content-Type: application/json
Authorization: Token {{token2}}

{
  "title": "Кресло (user2)",
  "description": "Комфортное, почти новое",
  "status": "OPEN"
}

###
# A4. Детали объявления user1 (анонимно)
GET {{baseUrl}}/advertisements/{{ad_id_user1}}/
Content-Type: application/json

# =====================================
#    БЛОК B: ФИЛЬТРАЦИЯ
# =====================================

###
# B1. По статусу (OPEN)
GET {{baseUrl}}/advertisements/?status=OPEN
Content-Type: application/json

###
# B2. По статусу (CLOSED)
GET {{baseUrl}}/advertisements/?status=CLOSED
Content-Type: application/json

###
# B3. По автору (user1)
GET {{baseUrl}}/advertisements/?creator={{creator_id_user1}}
Content-Type: application/json

###
# B4. По автору (user2)
GET {{baseUrl}}/advertisements/?creator={{creator_id_user2}}
Content-Type: application/json

###
# B5. По интервалу дат (до даты)
GET {{baseUrl}}/advertisements/?created_at_before=2099-01-01T00:00:00
Content-Type: application/json

###
# B6. Комбинированный: статус=OPEN и автор=user1
GET {{baseUrl}}/advertisements/?status=OPEN&creator={{creator_id_user1}}
Content-Type: application/json

# =====================================
#    БЛОК C: ПРАВА ДОСТУПА (permissions)
# =====================================

###
# C1. user2 пытается изменить ЧУЖОЕ объявление user1 — ожидаем 403
PATCH {{baseUrl}}/advertisements/{{ad_id_user1}}/
Content-Type: application/json
Authorization: Token {{token2}}

{
  "status": "CLOSED"
}

###
# C2. user2 пытается удалить ЧУЖОЕ объявление user1 — ожидаем 403
DELETE {{baseUrl}}/advertisements/{{ad_id_user1}}/
Authorization: Token {{token2}}

###
# C3. Попытка удалить без токена — ожидаем 401
DELETE {{baseUrl}}/advertisements/{{ad_id_user1}}/

###
# C4. Владелец (user1) удаляет СВОЁ объявление — ожидаем 204
DELETE {{baseUrl}}/advertisements/{{ad_id_user1}}/
Authorization: Token {{token1}}

###
# C5. (зеркально) user1 пытается изменить ЧУЖОЕ объявление user2 — ожидаем 200 (так как user1 -- это Админ)
PATCH {{baseUrl}}/advertisements/{{ad_id_user2}}/
Content-Type: application/json
Authorization: Token {{token1}}

{
  "status": "CLOSED"
}

# =====================================
#    БЛОК D: ТРОТТЛИНГ (rate limit)
#    anon: 10/min  |  user: 20/min
# =====================================

# D1. Анонимный троттлинг — дерни подряд (>10 раз за минуту) → 429
###
GET {{baseUrl}}/advertisements/

###
# D2. Троттлинг авторизованного (user1) — дерни подряд (>20 раз за минуту) → 429
GET {{baseUrl}}/advertisements/  
Authorization: Token {{token1}}

# =====================================
#    БЛОК E: Валидация (11-е OPEN = 400)
# =====================================

###
#  Создай 10 объявлений OPEN от user1 (используй @token1)
# 11-я попытка создать OPEN — ожидаем 400 ValidationError
# По достижению ОБЩЕГО числа созданных объявлений 10
# на запрос 11-го объявления — 400 ValidationError
# Дёрни 11 раз запрос
POST {{baseUrl}}/advertisements/
Content-Type: application/json
Authorization: Token {{token1}}

{
  "title": "OPEN demo",
  "description": "demo",
  "status": "OPEN"
}

# =====================================
#    БЛОК F: Избранные объявления
# =====================================

###
# F1. Добавить в избранное как user2 чужое объявление (user1)
POST {{baseUrl}}/advertisements/{{ad_id_user1}}/favorite/
Authorization: Token {{token2}}

###
# F2. Попытка добавить СВОЁ объявление в избранное (ожидаем 400)
POST {{baseUrl}}/advertisements/{{ad_id_user1}}/favorite/
Authorization: Token {{token1}}

###
# F3. Список МОИХ избранных (user2)
GET {{baseUrl}}/advertisements/favorites/
Authorization: Token {{token2}}

###
# F4. Фильтр по избранным в ОБЩЕМ списке (user2)
GET {{baseUrl}}/advertisements/?favorite=true
Authorization: Token {{token2}}

# =====================================
#    БЛОК G: Видимость DRAFT
# =====================================
# Шаг 0: создаём объявление в статусе DRAFT от user1 и user2
# ВАЖНО: подставляйте реальные id созданных DRAFT в @draftUser1/@draftUser2

@draftUser2 = 30
@draftUser1 = 31

### @name create_draft_user2
POST {{baseUrl}}/advertisements/
Content-Type: application/json
Authorization: Token {{token2}}

{
  "title": "DRAFT demo (user2)",
  "description": "виден только автору и админу",
  "status": "DRAFT"
}

### @name create_draft_user1
POST {{baseUrl}}/advertisements/
Content-Type: application/json
Authorization: Token {{token1}}

{
  "title": "DRAFT demo (user1)",
  "description": "виден только автору и админу",
  "status": "DRAFT"
}

###
# G0.1 Автор (user2) получает детали своего DRAFT — ожидаем 200
GET {{baseUrl}}/advertisements/{{draftUser2}}/
Authorization: Token {{token2}}

###
# G1. Автор (user2) видит СВОИ DRAFT в списке — ожидаем, что есть как минимум 1 запись
GET {{baseUrl}}/advertisements/?status=DRAFT
Authorization: Token {{token2}}

###
# G2. Другой пользователь (user2) НЕ видит DRAFT автора (user1) в списке — ожидаем список без DRAFT от user1
GET {{baseUrl}}/advertisements/?status=DRAFT
Authorization: Token {{token2}}

###
# G2.1 Другой пользователь (user2) попробует открыть детали конкретного DRAFT — ожидаем 404
GET {{baseUrl}}/advertisements/{{draftUser1}}/
Authorization: Token {{token2}}

###
# G3. Админ видит все DRAFT (если token1 — админ) — ожидаем, что запись видна
GET {{baseUrl}}/advertisements/?status=DRAFT
Authorization: Token {{token1}}

### 
# G3.1 Админ/автор может перевести DRAFT → OPEN, после чего его увидят все
PATCH {{baseUrl}}/advertisements/{{draftUser2}}/
Content-Type: application/json
Authorization: Token {{token1}}

{
  "status": "OPEN"
}

```
</details>

---

## Скриншоты по запросам

Положи скриншоты в `docs/screenshots/` и вставь сюда:
### Получение и добавление токенов
- 1 ![Get_user1_token](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20133116.png)
- 2 ![Get_user2_token](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20133141.png)
  
### A — создание/база
- A1 ![A1_list](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20133239.png)
- A2 ![A2_create_user1](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20133311.png)
- A3 ![A3_create_user2](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20133351.png)
- A4 ![A4_detail_user1](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20133519.png)

### B — фильтрация
- B1 ![B1_open](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20133543.png)
- B2 ![B2_closed](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20133606.png)
- B3 ![B3_creator_user1](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20133633.png)
- B4 ![B4_creator_user2](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20133655.png)
- B5 ![B5_date_before](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20133719.png)
- B6 ![B6_open_user1](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20133745.png)

### C — права
- C1 ![C1_patch_foreign_403](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20134215.png)
- C2 ![C2_delete_foreign_403](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20134242.png)
- C3 ![C3_delete_no_token_401](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20134302.png)
- C4 ![C4_delete_own_204](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20134323.png)
- C5 ![C5_admin_or_forbidden](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20134352.png)

### D — троттлинг
- D1 ![D1_throttle_anon_429](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20134422.png)
- D2 ![D2_throttle_user_429](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20134456.png)

### E — валидация
- E11 ![E11_open_400](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20134646.png)

### F — избранное
- F1 ![F1_favorite_add](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20135449.png)
- F2 ![F2_favorite_self_400](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20135634.png)
- F3 ![F3_favorites_list](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20135659.png)
- F4 ![F4_favorites_filter](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20135723.png)

### G — DRAFT
- 00.1 ![Create_druft_massage_user2](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20144912.png)
- 00.1 ![Create_draft_message_user1](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20144956.png)
- G0.1 ![G0_1_get_draft_author](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20145903.png)
- G1 ![G1_draft_list_author](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20145936.png)
- G2.1 ![G2_1_draft_detail_404](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20150500.png)
- G3 ![G3_draft_list_admin](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20150546.png)
- G3.1 ![G3_1_draft_to_open](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20150858.png)

---

## Скриншоты админки

- Пользователи — `https://127.0.0.1:8000/admin/auth/user/`  
  ![Admin-Users](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20133032.png)

- Токены — `https://127.0.0.1:8000/admin/authtoken/tokenproxy/`  
  ![Admin-Tokens](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20132941.png)

- Объявления — `https://127.0.0.1:8000/admin/advertisements/advertisement/`  
  ![Admin-Advertisements](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20151156.png)

- Избранные — `https://127.0.0.1:8000/admin/advertisements/favorite/`  
  ![Admin-Favorites](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-11-13%20151136.png)

---

## Диаграмма БД (DBeaver)
![DB-Diagram](https://github.com/VoldemarSoturum/HW-7-7-DJANGO-REAST_API_Permissions/blob/main/EX1-API_WITH_RESTRICTIONS/OUT_DATA_7-7/netology_app_advertisements%20-%20public.png)

---

## Отладка и частые проблемы

- **404 на F1** — объявление удалено ранее (C4) или это DRAFT чужого пользователя. Проверь `GET /advertisements/{ad_id_user1}/` под `token2` → 200 и `status=OPEN`.
- **404 на G0.1** — проверь, что `@draftUser2/@draftUser1` — реальные id из ответа POST.
- **WRONG_VERSION_NUMBER** — стучишься по HTTPS к HTTP-серверу. Запускай `runserver_plus`.
- **401** — нет/неверный токен в заголовке `Authorization: Token <TOKEN>`.
- **403** — попытка правки/удаления чужого объекта. Админ может всё (is_staff=True).
- **429** — срабатывает троттлинг (это норма при D-блоке).
- **Фильтры** — нужна установка `django-filter` и `DjangoFilterBackend` в настройках DRF.
- **`obtain_auth_token` не импортирован** — добавь `from rest_framework.authtoken.views import obtain_auth_token` в `urls.py`.
- **PostgreSQL** — проверь креды/порт/доступ; для быстрой проверки можно временно перейти на SQLite.

---

## Структура проекта (фрагмент)
```
api_with_restrictions/
├─ api_with_restrictions/
│  ├─ settings.py
│  └─ urls.py
├─ advertisements/
│  ├─ models.py
│  ├─ serializers.py
│  ├─ views.py
│  ├─ filters.py
│  ├─ permissions.py
│  └─ admin.py
└─ manage.py
```
```
API with Restrictions — Справка по ответам сервера (TXT)

Легенда статусов:
200 OK            — Успешно (возвращает JSON)
201 Created       — Создано (возвращает JSON созданного объекта)
204 No Content    — Успешно (тело пустое)
400 Bad Request   — Ошибка валидации/данных запроса
401 Unauthorized  — Нет или неверные учетные данные (токен)
403 Forbidden     — Нет прав (не владелец и не админ), но аутентификация есть
404 Not Found     — Объект не найден или скрыт политикой видимости (например, чужой DRAFT)
429 Too Many Requests — Превышен лимит запросов (троттлинг)

Общие заголовки ответа: Content-Type: application/json (кроме 204)
DRF тексты по умолчанию: "Authentication credentials were not provided.", "You do not have permission to perform this action.",
"Request was throttled. Expected available in X seconds.", и т.д.

==============================================================================================
| Контекст / Endpoint                                        | Метод  | Треб. Auth | Возможные статусы и когда                                         |
|------------------------------------------------------------|--------|------------|-------------------------------------------------------------------|
| Получить токен: /api-token-auth/                           | POST   | нет        | 200 — валидные логин/пароль ({"token": "…"})                      |
|                                                            |        |            | 400 — неверные креды / невалидный JSON                            |
| Список объявлений: /api/advertisements/                    | GET    | нет        | 200 — список                                                       |
|                                                            |        |            | 429 — превышен лимит (anon 10/мин, user 20/мин)                   |
| Создать объявление: /api/advertisements/                   | POST   | да         | 201 — создано                                                      |
|                                                            |        |            | 400 — валидация (например, >10 OPEN у автора)                     |
|                                                            |        |            | 401 — нет токена                                                   |
|                                                            |        |            | 429 — троттлинг                                                    |
| Детали объявления: /api/advertisements/{id}/               | GET    | нет        | 200 — найден                                                       |
|                                                            |        |            | 404 — нет такого id или чужой DRAFT                               |
|                                                            |        |            | 429 — троттлинг                                                    |
| Изменить объявление: /api/advertisements/{id}/             | PATCH  | да         | 200 — изменено                                                     |
|                                                            |        |            | 400 — валидация (например, перевод в OPEN при лимите)             |
|                                                            |        |            | 401 — нет токена                                                   |
|                                                            |        |            | 403 — не владелец и не админ                                       |
|                                                            |        |            | 404 — нет такого id / не видно (чужой DRAFT)                      |
|                                                            |        |            | 429 — троттлинг                                                    |
| Удалить объявление: /api/advertisements/{id}/              | DELETE | да         | 204 — удалено                                                      |
|                                                            |        |            | 401 — нет токена                                                   |
|                                                            |        |            | 403 — не владелец и не админ                                       |
|                                                            |        |            | 404 — нет такого id / не видно (чужой DRAFT)                      |
|                                                            |        |            | 429 — троттлинг                                                    |
| Добавить в избранное: /api/advertisements/{id}/favorite/   | POST   | да         | 201 — добавлено в избранное                                        |
|                                                            |        |            | 200 — уже было в избранном (idempotent get_or_create)             |
|                                                            |        |            | 400 — нельзя добавить своё объявление                              |
|                                                            |        |            | 401 — нет токена                                                   |
|                                                            |        |            | 404 — id не существует или не виден (например, чужой DRAFT)       |
|                                                            |        |            | 429 — троттлинг                                                    |
| Удалить из избранного: /api/advertisements/{id}/unfavorite/| DELETE | да         | 204 — удалено (idempotent; ок даже если записи не было)           |
|                                                            |        |            | 401 — нет токена                                                   |
|                                                            |        |            | 404 — id не существует или не виден                               |
|                                                            |        |            | 429 — троттлинг                                                    |
| Мои избранные: /api/advertisements/favorites/              | GET    | да         | 200 — список                                                       |
|                                                            |        |            | 401 — нет токена                                                   |
|                                                            |        |            | 429 — троттлинг                                                    |
| Фильтрация (query params: creator, status, dates, favorite)| GET    | см. выше   | 200 — список (пустой, если ничего не найдено)                     |
|                                                            |        |            | 429 — троттлинг                                                    |
==============================================================================================

Дополнительно по бизнес-правилам/видимости:
- Статус DRAFT видят только автор и админ. Для остальных детальный доступ вернёт 404.
- Лимит объявлений OPEN: у одного пользователя не более 10. 11-я попытка создания/перевода в OPEN → 400.
- Админ (is_staff=True) может редактировать/удалять любые объявления (200/204 вместо 403).
- Троттлинг DRF: anon — 10/мин, user — 20/мин. Превышение → 429 с текстом ожидания.
```
