.PHONY: up down build restart \
        logs logs-app logs-publisher logs-consumer \
        migrate shell-app shell-postgres ps

# ─── Запуск / остановка ───────────────────────────────────────────────────────

## Собрать образы и запустить все сервисы
up:
	docker compose up -d --build

## Остановить все сервисы и удалить контейнеры
down:
	docker compose down

## Только собрать образы (без запуска)
build:
	docker compose build

## Перезапустить все сервисы
restart:
	docker compose restart

## Посмотреть статус контейнеров
ps:
	docker compose ps

# ─── Логи ─────────────────────────────────────────────────────────────────────

## Все логи (follow)
logs:
	docker compose logs -f

## Логи FastAPI приложения
logs-app:
	docker compose logs -f app

## Логи publisher (outbox worker)
logs-publisher:
	docker compose logs -f publisher

## Логи consumer (rabbitmq worker)
logs-consumer:
	docker compose logs -f consumer

# ─── Миграции ─────────────────────────────────────────────────────────────────

## Применить миграции Alembic
migrate:
	docker compose run --rm migrate

## Создать новую миграцию (использование: make migration name=add_payments_table)
migration:
	docker compose run --rm -w /app/src migrate \
		alembic -c alembic.ini revision --autogenerate -m "$(name)"

# ─── Утилиты ──────────────────────────────────────────────────────────────────

## Открыть bash в контейнере app
shell-app:
	docker compose exec app bash

## Открыть psql в контейнере postgres
shell-postgres:
	docker compose exec postgres psql -U postgres -d db


