# 💳 Asyncio Payment Processing

Асинхронный сервис обработки платежей на **FastAPI + RabbitMQ + PostgreSQL**.  
Реализует паттерн **Transactional Outbox** для надёжной доставки событий.

---

## 📐 Архитектура

```
┌─────────────┐   HTTP    ┌─────────────────┐   SQL    ┌──────────────┐
│   Client    │ ────────► │   FastAPI App   │ ───────► │  PostgreSQL  │
└─────────────┘           │   (port 8000)   │          │  - payments  │
                          └────────┬────────┘          │  - outbox    │
                                   │ writes outbox      └──────┬───────┘
                                   │                           │
                          ┌────────▼────────┐                  │ polls
                          │   Publisher     │ ◄────────────────┘
                          │ (Outbox Worker) │
                          └────────┬────────┘
                                   │ publish
                          ┌────────▼────────┐
                          │    RabbitMQ     │
                          │ payments.new    │
                          │ payments.dead   │
                          └────────┬────────┘
                                   │ consume
                          ┌────────▼────────┐   SQL    ┌──────────────┐
                          │    Consumer     │ ───────► │  PostgreSQL  │
                          │ (RabbitMQ Worker│          │ update status│
                          └─────────────────┘          └──────────────┘
```

### Сервисы

| Сервис | Описание |
|--------|----------|
| **app** | FastAPI — принимает HTTP-запросы, создаёт платежи и события outbox |
| **publisher** | Outbox Worker — опрашивает БД, публикует события в RabbitMQ |
| **consumer** | RabbitMQ Worker — обрабатывает платежи, обновляет статусы, отправляет webhook |
| **postgres** | БД: таблицы `payments` и `outbox_events` |
| **rabbitmq** | Брокер: очередь `payments.new` + DLQ `payments.dead` |

### Паттерны

- **Transactional Outbox** — создание платежа и события в одной транзакции
- **Idempotency Key** — защита от дублирования запросов
- **Dead Letter Queue** — автоматический retry + DLQ после N попыток
- **Unit of Work** — управление транзакциями через UoW

---

## 🗂️ Структура проекта

```
.
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── .env.app          # FastAPI настройки
├── .env.db           # PostgreSQL настройки
├── .env.broker       # RabbitMQ настройки
├── .env.publisher    # Outbox Worker настройки
├── .env.consumer     # Consumer настройки
├── .env.httpx        # HTTP-клиент настройки
└── src/
    ├── main.py           # FastAPI точка входа
    ├── publisher.py      # Publisher точка входа
    ├── consumer.py       # Consumer точка входа
    ├── alembic.ini
    ├── alembic/
    │   └── versions/     # Миграции БД
    ├── api/              # Роуты и зависимости
    ├── core/             # Конфиг, БД, RabbitMQ, HTTP-клиент
    ├── messaging/        # Publisher и Consumer классы
    ├── models/           # SQLAlchemy модели
    ├── repositories/     # Слой доступа к данным
    ├── schemas/          # Pydantic схемы
    └── services/         # Бизнес-логика
```

---

## ⚙️ Требования

- **Docker** ≥ 24.0
- **Docker Compose** ≥ 2.20
- **Make** (опционально, для Makefile-команд)

---

## 🚀 Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone https://github.com/Stepan1771/asyncio-payment-processing.git
cd asyncio-payment-processing
```

### 2. Проверить env-файлы

Все `.env.*` файлы уже настроены для локального запуска. При необходимости измените:

```bash
# .env.app — API ключ и порт приложения
APP_CONFIG__AUTH__API_KEY=secret-api-key
APP_CONFIG__APP__PORT=8000

# .env.db — параметры PostgreSQL
DB_CONFIG__DB__HOST=postgres
DB_CONFIG__DB__USER=postgres
DB_CONFIG__DB__PASSWORD=postgres
DB_CONFIG__DB__NAME=db

# .env.broker — параметры RabbitMQ
BROKER_CONFIG__BROKER__HOST=rabbitmq
BROKER_CONFIG__BROKER__USER=guest
BROKER_CONFIG__BROKER__PASSWORD=guest
```

### 3. Запустить через Make (рекомендуется)

```bash
make up
```

Эта команда:
1. Собирает Docker-образы
2. Запускает PostgreSQL и RabbitMQ
3. Выполняет миграции БД (`alembic upgrade head`)
4. Запускает `app`, `publisher`, `consumer`

### 3a. Или напрямую через Docker Compose

```bash
docker compose up -d --build
```

### 4. Убедиться, что всё запущено

```bash
make ps
# или
docker compose ps
```

Ожидаемый вывод:

```
NAME        STATUS          PORTS
app         Up              0.0.0.0:8000->8000/tcp
consumer    Up
publisher   Up
postgres    Up (healthy)    0.0.0.0:5432->5432/tcp
rabbitmq    Up (healthy)    0.0.0.0:5672->5672/tcp, 0.0.0.0:15672->15672/tcp
```

---

## 🗄️ Миграции

Миграции применяются автоматически при `make up` через сервис `migrate`.

### Создать новую миграцию (после изменений модели)

```bash
make migration name=add_new_field
```

### Применить миграции вручную

```bash
make migrate
```

---

## 🔍 Проверка работоспособности

> Все запросы требуют заголовок `X-API-Key: secret-api-key`

### 1. Создать платёж

```bash
curl -X POST http://localhost:8000/api/v1/payments/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret-api-key" \
  -H "Idempotency-Key: unique-key-001" \
  -d '{
    "amount": "100.50",
    "currency": "RUB",
    "description": "Оплата заказа #1234",
    "webhook_url": "http://httpbin.org/post"
  }'
```

**Ответ (202 Accepted):**
```json
{
  "id": 1,
  "status": "pending",
  "created_at": "2026-04-07T12:47:27.832801Z"
}
```

---

### 2. Получить информацию о платеже

```bash
curl http://localhost:8000/api/v1/payments/1 \
  -H "X-API-Key: secret-api-key"
```

**Ответ (200 OK):**
```json
{
  "id": 1,
  "uid": "56c9ea67-554a-47c3-a50e-1e47571bf06a",
  "amount": "100.50",
  "currency": "RUB",
  "description": "Оплата заказа #1234",
  "metadata": null,
  "status": "pending",
  "idempotency_key": "unique-key-001",
  "webhook_url": "http://httpbin.org/post",
  "created_at": "2026-04-07T12:47:27.832801Z",
  "updated_at": "2026-04-07T12:47:27.832801Z"
}
```

Через 2–10 секунд статус изменится на `succeeded` или `failed` (после обработки consumer'ом).

---

### 3. Проверить идемпотентность

Повторный запрос с тем же `Idempotency-Key` должен вернуть **тот же** платёж без дубликата:

```bash
curl -X POST http://localhost:8000/api/v1/payments/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret-api-key" \
  -H "Idempotency-Key: unique-key-001" \
  -d '{
    "amount": "999.00",
    "currency": "USD",
    "description": "Другой платёж — но тот же ключ",
    "webhook_url": "http://httpbin.org/post"
  }'
```

**Ответ:** тот же `id=1`, `status=pending` — дубликат не создан.

---

### 4. Проверить авторизацию

Запрос без ключа → 403:

```bash
curl http://localhost:8000/api/v1/payments/1
# → 403 Forbidden: {"detail": "Invalid or missing X-API-Key header"}
```

Неверный ключ → 403:

```bash
curl http://localhost:8000/api/v1/payments/1 \
  -H "X-API-Key: wrong-key"
# → 403 Forbidden
```

---

### 5. Создать платёж с metadata

```bash
curl -X POST http://localhost:8000/api/v1/payments/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret-api-key" \
  -H "Idempotency-Key: unique-key-002" \
  -d '{
    "amount": "250.00",
    "currency": "USD",
    "description": "Подписка Premium",
    "metadata": {"user_id": 42, "plan": "premium"},
    "webhook_url": "http://httpbin.org/post"
  }'
```

---

### 6. Полный E2E тест (bash)

```bash
#!/bin/bash
KEY="e2e-test-$(date +%s)"

# 1. Создать платёж
echo "=== Создание платежа ==="
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/payments/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret-api-key" \
  -H "Idempotency-Key: $KEY" \
  -d '{"amount":"50.00","currency":"RUB","description":"E2E test","webhook_url":"http://httpbin.org/post"}')
echo $RESPONSE
ID=$(echo $RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 2. Ждём обработки
echo "=== Ожидание обработки (15 сек) ==="
sleep 15

# 3. Проверить статус
echo "=== Статус платежа #$ID ==="
curl -s http://localhost:8000/api/v1/payments/$ID \
  -H "X-API-Key: secret-api-key" | python3 -m json.tool
```

---

## 📋 Просмотр логов

```bash
# Логи FastAPI приложения
make logs-app

# Логи Publisher (Outbox Worker)
make logs-publisher

# Логи Consumer (RabbitMQ Worker)
make logs-consumer

# Все логи сразу
make logs
```

### Пример логов Publisher

```
INFO  messaging.publishers.outbox:start          - Запуск outbox worker
INFO  messaging.publishers.outbox:_publish_event - Публикация ивента: outbox_event_id - 1
INFO  messaging.publishers.outbox:_process_batch - Всего ивентов: 1, Опубликовано: 1, Ошибок: 0
```

### Пример логов Consumer

```
INFO  - FastStream app starting...
INFO  - payments  payments.new  - `MainHandler` waiting for messages
INFO  - payments  payments.new  abc123 - Received
INFO  messaging.consumers.payment:_payment_simulator - Эмуляция платежного шлюза
INFO  - payments  payments.new  abc123 - Processed
```

---

## 🛠️ Makefile — справка команд

```bash
make up              # Собрать образы и запустить все сервисы
make down            # Остановить и удалить контейнеры
make build           # Только собрать образы
make restart         # Перезапустить все сервисы
make ps              # Статус контейнеров

make logs            # Все логи (follow)
make logs-app        # Логи FastAPI
make logs-publisher  # Логи Publisher
make logs-consumer   # Логи Consumer

make migrate                        # Применить миграции
make migration name=add_payments    # Создать новую миграцию

make shell-app       # bash внутри контейнера app
make shell-postgres  # psql в PostgreSQL
```

---

## 🐰 RabbitMQ Management UI

После запуска доступен веб-интерфейс:

- **URL:** http://localhost:15672
- **Login:** `guest`
- **Password:** `guest`

Там можно видеть очереди `payments.new` и `payments.dead`, exchanges, количество сообщений.

---

## 🗃️ Прямой доступ к PostgreSQL

```bash
make shell-postgres
# или
docker compose exec postgres psql -U postgres -d db
```

```sql
-- Все платежи
SELECT id, uid, amount, currency, status, created_at FROM payments ORDER BY id;

-- Outbox события
SELECT id, processed, created_at FROM outbox_events ORDER BY id;

-- Статистика по статусам
SELECT status, COUNT(*) FROM payments GROUP BY status;
```

---

## 🔧 Локальная разработка (без Docker)

### Требования
- Python 3.13+
- [uv](https://docs.astral.sh/uv/)

### Установка

```bash
uv sync
```

### Запуск инфраструктуры (только Postgres + RabbitMQ)

```bash
docker compose up -d postgres rabbitmq
```

### Применить миграции

```bash
cd src
alembic -c alembic.ini upgrade head
```

### Запустить сервисы локально

```bash
# Терминал 1 — FastAPI
cd src && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Терминал 2 — Publisher
cd src && python publisher.py

# Терминал 3 — Consumer
cd src && python consumer.py
```

---

## 🌍 Переменные окружения

### `.env.app`
| Переменная | Описание | Пример |
|-----------|----------|--------|
| `APP_CONFIG__APP__SERVICE_NAME` | Имя сервиса | `payment-service` |
| `APP_CONFIG__APP__HOST` | Хост uvicorn | `0.0.0.0` |
| `APP_CONFIG__APP__PORT` | Порт uvicorn | `8000` |
| `APP_CONFIG__AUTH__API_KEY` | API-ключ авторизации | `secret-api-key` |

### `.env.db`
| Переменная | Описание | Пример |
|-----------|----------|--------|
| `DB_CONFIG__DB__HOST` | Хост PostgreSQL | `postgres` |
| `DB_CONFIG__DB__PORT` | Порт | `5432` |
| `DB_CONFIG__DB__USER` | Пользователь | `postgres` |
| `DB_CONFIG__DB__PASSWORD` | Пароль | `postgres` |
| `DB_CONFIG__DB__NAME` | Имя БД | `db` |
| `DB_CONFIG__DB__POOL_SIZE` | Размер пула соединений | `5` |

### `.env.broker`
| Переменная | Описание | Пример |
|-----------|----------|--------|
| `BROKER_CONFIG__BROKER__HOST` | Хост RabbitMQ | `rabbitmq` |
| `BROKER_CONFIG__BROKER__PORT` | AMQP порт | `5672` |
| `BROKER_CONFIG__BROKER__USER` | Пользователь | `guest` |
| `BROKER_CONFIG__BROKER__PASSWORD` | Пароль | `guest` |
| `BROKER_CONFIG__BROKER__PAYMENTS_EXCHANGE` | Основной exchange | `payments` |
| `BROKER_CONFIG__BROKER__PAYMENTS_QUEUE` | Основная очередь | `payments.new` |
| `BROKER_CONFIG__BROKER__PAYMENTS_DLX_EXCHANGE` | DLX exchange | `payments.dlx` |
| `BROKER_CONFIG__BROKER__PAYMENTS_DEAD_QUEUE` | DLQ очередь | `payments.dead` |

### `.env.publisher`
| Переменная | Описание | Пример |
|-----------|----------|--------|
| `PUBLISHER_CONFIG__OUTBOX_WORKER__POLL_INTERVAL` | Интервал опроса БД (сек) | `2` |
| `PUBLISHER_CONFIG__OUTBOX_WORKER__BATCH_SIZE` | Размер батча событий | `100` |
| `PUBLISHER_CONFIG__OUTBOX_WORKER__ERROR_BACKOFF` | Пауза при ошибке (сек) | `5` |

### `.env.consumer`
| Переменная | Описание | Пример |
|-----------|----------|--------|
| `CONSUMER_CONFIG__CONSUMER__MAX_RETRIES` | Макс. попыток retry | `3` |

---

## 📡 API Reference

### `POST /api/v1/payments/`

Создание платежа.

**Headers:**
- `X-API-Key: <key>` — обязательный
- `Idempotency-Key: <uuid>` — обязательный, уникальный ключ для защиты от дублирования
- `Content-Type: application/json`

**Body:**
```json
{
  "amount": "100.50",
  "currency": "RUB",
  "description": "Описание платежа",
  "metadata": {"key": "value"},
  "webhook_url": "https://your-server.com/webhook"
}
```

| Поле | Тип | Обязательный | Описание |
|------|-----|:---:|---------|
| `amount` | decimal | ✅ | Сумма > 0, 2 знака после запятой |
| `currency` | enum | ✅ | `RUB`, `USD`, `EUR` |
| `description` | string | ✅ | 1–500 символов |
| `metadata` | object | ❌ | Произвольные метаданные |
| `webhook_url` | string | ✅ | URL для webhook-уведомления |

**Ответы:**
- `202 Accepted` — платёж создан (или найден по idempotency key)
- `403 Forbidden` — неверный или отсутствующий API ключ
- `422 Unprocessable Entity` — ошибка валидации

---

### `GET /api/v1/payments/{payment_id}`

Получение платежа по ID.

**Headers:**
- `X-API-Key: <key>` — обязательный

**Ответы:**
- `200 OK` — данные платежа
- `403 Forbidden` — неверный API ключ

**Статусы платежа:**
| Статус | Описание |
|--------|----------|
| `pending` | Ожидает обработки |
| `succeeded` | Успешно обработан |
| `failed` | Обработка завершилась ошибкой |
