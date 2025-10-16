# Finance Assistant — Backend

Бэкенд сервиса  **«Финансовый помощник»** : принимает ручные расходы и загруженные чеки (фото), извлекает из них данные (ML составляющая OCR), автоматически категоризирует траты (напр. «еда», «транспорт», «развлечения»), строит агрегаты для графиков и формирует советы по экономии.

## Стек

- **Python 3.11+**
- **FastAPI** (ASGI) — REST + Swagger UI
- **PostgreSQL** — основная БД
- **SQLAlchemy 2.0** + **asyncpg**
- **Alembic** — миграции схемы

## Быстрый старт

### 1) Установка Poetry

Рекомендуемый способ — через `pipx` или официальный установщик:

```bash
pipx install poetry
# или
python -m pip install --user poetry
poetry --version
```

### 2) Клонирование и зависимости

```bash
poetry install
```

### 3) Запуск приложения

```bash
poetry run python -m app.main
# Документация будет доступна на: http://localhost:8000/docs
```

---
## API — Swagger UI / OpenAPI

**Ссылки (локально):**
- Swagger UI: `http://localhost:8000/docs`

**Базовый префикс API:** `/api/v1`

### Авторизация в Swagger UI (Bearer JWT)

1) Пройди флоу: `request-code` → `verify-code` → `set-password` → `login`.  
2) Возьми **access token** из ответа `login`.  
3) В Swagger нажми **Authorize** → введи `Bearer <access_token>` → **Authorize**.  
4) Дальше защищённые эндпоинты вызываются с заголовком `Authorization: Bearer <access_token>`.

---

### Эндпоинты (как в Swagger UI)

#### `health`
| Метод | Путь                                    | Описание                            |
|------:|-----------------------------------------|-------------------------------------|
| GET   | `/api/v1/health`                        | Health                              |
| GET   | `/api/v1/health/db`                     | Db Health                           |
| GET   | `/api/v1/health/db/auth/email_codes`    | Check Auth (email codes)            |
| GET   | `/api/v1/health/db/auth/refresh_tokens` | Check Auth (refresh tokens)         |
| GET   | `/api/v1/health/db/auth/users`          | Check Auth (users)                  |
| GET   | `/api/v1/health/readiness`              | Readiness                           |

#### `auth`
| Метод | Путь                   | Описание                                      |
|------:|------------------------|-----------------------------------------------|
| POST  | `/api/v1/request-code` | Отправить код на email                        |
| POST  | `/api/v1/verify-code`  | Проверить код из email                        |
| POST  | `/api/v1/set-password` | Установить пароль и получить JWT              |
| POST  | `/api/v1/login`        | Вход (email + password) → access/refresh      |
| POST  | `/api/v1/refresh`      | Обновить access/refresh по refresh            |
| POST  | `/api/v1/logout`       | Logout (отозвать refresh-токен)               |

#### `expenses`
| Метод | Путь                    | Описание                       |
|------:|-------------------------|--------------------------------|
| GET   | `/api/v1/expenses`      | Get Expenses                   |
| POST  | `/api/v1/expenses`      | Create Expense                 |
| GET   | `/api/v1/expenses/{id}` | Get Expense By Id              |
| PATCH | `/api/v1/expenses/{id}` | Update Expense (partial)       |
| DELETE| `/api/v1/expenses/{id}` | Delete Expense                 |

#### `receipts`
| Метод | Путь               | Описание    |
|------:|--------------------|-------------|
| POST  | `/api/v1/receipts` | Add Receipt |

#### `analytics`
| Метод | Путь                            | Описание                     |
|------:|---------------------------------|------------------------------|
| GET   | `/api/v1/analytics/timeseries`  | Get Timeseries               |
| GET   | `/api/v1/analytics/by-category` | Get Timeseries By Category   |

#### `categories`
| Метод | Путь                 | Описание      |
|------:|----------------------|---------------|
| GET   | `/api/v1/categories` | Get Statistic |

#### `advice`
| Метод | Путь            | Описание       |
|------:|-----------------|----------------|
| GET   | `/api/v1/advice`| Get Timeseries |

#### `root`
| Метод | Путь | Описание |
|------:|------|----------|
| GET   | `/`  | Root     |

---

### Pydantic-схемы (раздел **Schemas** в Swagger)
`CodeVerifyIn`, `CodeVerifyOut`, `EmailIn`, `HTTPValidationError`, `LoginIn`, `LogoutIn`, `RefreshIn`, `RequestCodeOut`, `SetPasswordIn`, `TokensOut`, `ValidationError`.



---

## Минимальная модель данных (MVP)

Используются 5 таблиц:

- **users** — учётная запись
- **accounts** — счета пользователя (валюта, название)
- **categories** — категории доходов/расходов (income|expense)
- **transactions** — операции (user, account, category, amount, date, description)
- **receipts** — загруженные файлы чеков и извлечённые метаданные (file_path, merchant, total)

---

## Сквозные сценарии

### Ручной ввод

Пользователь выбирает счёт и категорию, вводит сумму и дату → создаётся запись в `transactions`.

### Загрузка чека

Файл сохраняется в `RECEIPTS_DIR`, создаётся запись в `receipts`. OCR/ML извлекает сумму/магазин/дату и предлагает категорию; пользователь подтверждает → создаётся `transactions`, поле `receipts.transaction_id` заполняется ссылкой на неё.

---

## Разработка

Запуск утилит (если подключены как dev-зависимости):

```bash
# тесты
poetry run pytest -q

# линтеры/форматирование/тайпчек
poetry run ruff check .
poetry run black --check .
poetry run mypy .
```

Запуск в интерактивном окружении:

```bash
poetry shell
python -m app.main
```

## Точки роста (после MVP)

- Хранилище файлов → S3/MinIO (подписанные URL)
- Детализация чеков (`receipt_items`) и сплит по категориям
- Бюджеты, кэш балансов, расширенная аналитика
- Логи ML и мониторинг качества извлечения

---

## Use-case диаграмма

Диаграмма демонстрирует основные сценарии взаимодействия пользователя с системой: добавление расходов вручную, загрузку чеков с автоматическим извлечением данных (OCR/ML), категоризацию транзакций и получение аналитических советов.


<table align="center">
  <tr>
    <td align="center">
      <img src="docs/use-case-diagram.png" alt="Use-case Diagram" width="800"/>
    </td>
  </tr>
</table>

<br><br>
<b>Варианты использования для роли «Неавторизованный пользователь»</b>
<table align="center">
  <tr>
    <td align="center">
      <img src="docs/not-authorized-user.png" alt="not-authorized-user diagram" width="800"/>
    </td>
  </tr>
</table>

<br><br>
<b>Варианты использования для роли «Администратор»</b>
<table align="center">
  <tr>
    <td align="center">
      <img src="docs/admin-user.png" alt="admin-user diagram" width="800"/>
    </td>
  </tr>
</table>
