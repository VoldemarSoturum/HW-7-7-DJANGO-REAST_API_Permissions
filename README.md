# API with Restrictions (DRF): Фильтрация, Валидация, Аутентификация, Троттлинг + Избранное и DRAFT

Учебный проект по Django REST Framework. Реализовано:
- Аутентификация по токену (DRF authtoken).
- Права: читать — всем; **менять/удалять** — **владелец** или **админ** (is_staff).
- Фильтрация по автору, статусу (`OPEN/CLOSED/DRAFT`), интервалам даты.
- Бизнес-валидация: не более **10** объявлений в статусе **OPEN** на пользователя.
- Троттлинг: **anon 10/мин**, **user 20/мин**.
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

### A — создание/база
- A1 ![A1_list](docs/screenshots/A1_list.png)
- A2 ![A2_create_user1](docs/screenshots/A2_create_user1.png)
- A3 ![A3_create_user2](docs/screenshots/A3_create_user2.png)
- A4 ![A4_detail_user1](docs/screenshots/A4_detail_user1.png)

### B — фильтрация
- B1 ![B1_open](docs/screenshots/B1_open.png)
- B2 ![B2_closed](docs/screenshots/B2_closed.png)
- B3 ![B3_creator_user1](docs/screenshots/B3_creator_user1.png)
- B4 ![B4_creator_user2](docs/screenshots/B4_creator_user2.png)
- B5 ![B5_date_before](docs/screenshots/B5_date_before.png)
- B6 ![B6_open_user1](docs/screenshots/B6_open_user1.png)

### C — права
- C1 ![C1_patch_foreign_403](docs/screenshots/C1_patch_foreign_403.png)
- C2 ![C2_delete_foreign_403](docs/screenshots/C2_delete_foreign_403.png)
- C3 ![C3_delete_no_token_401](docs/screenshots/C3_delete_no_token_401.png)
- C4 ![C4_delete_own_204](docs/screenshots/C4_delete_own_204.png)
- C5 ![C5_admin_or_forbidden](docs/screenshots/C5_admin_or_forbidden.png)

### D — троттлинг
- D1 ![D1_throttle_anon_429](docs/screenshots/D1_throttle_anon_429.png)
- D2 ![D2_throttle_user_429](docs/screenshots/D2_throttle_user_429.png)

### E — валидация
- E1–E10 ![E1_E10_open_created](docs/screenshots/E1_E10_open_created.png)
- E11 ![E11_open_400](docs/screenshots/E11_open_400.png)

### F — избранное
- F1 ![F1_favorite_add](docs/screenshots/F1_favorite_add.png)
- F2 ![F2_favorite_self_400](docs/screenshots/F2_favorite_self_400.png)
- F3 ![F3_favorites_list](docs/screenshots/F3_favorites_list.png)
- F4 ![F4_favorites_filter](docs/screenshots/F4_favorites_filter.png)

### G — DRAFT
- G0.1 ![G0_1_get_draft_author](docs/screenshots/G0_1_get_draft_author.png)
- G1 ![G1_draft_list_author](docs/screenshots/G1_draft_list_author.png)
- G2 ![G2_draft_list_other](docs/screenshots/G2_draft_list_other.png)
- G2.1 ![G2_1_draft_detail_404](docs/screenshots/G2_1_draft_detail_404.png)
- G3 ![G3_draft_list_admin](docs/screenshots/G3_draft_list_admin.png)
- G3.1 ![G3_1_draft_to_open](docs/screenshots/G3_1_draft_to_open.png)

---

## Скриншоты админки

- Пользователи — `https://127.0.0.1:8000/admin/auth/user/`  
  ![Admin-Users](docs/screenshots/admin_users.png)

- Токены — `https://127.0.0.1:8000/admin/authtoken/tokenproxy/`  
  ![Admin-Tokens](docs/screenshots/admin_tokens.png)

- Объявления — `https://127.0.0.1:8000/admin/advertisements/advertisement/`  
  ![Admin-Advertisements](docs/screenshots/admin_advertisements.png)

- Избранные — `https://127.0.0.1:8000/admin/advertisements/favorite/`  
  ![Admin-Favorites](docs/screenshots/admin_favorites.png)

---

## Диаграмма БД (DBeaver)
![DB-Diagram](docs/screenshots/db_diagram.png)

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
