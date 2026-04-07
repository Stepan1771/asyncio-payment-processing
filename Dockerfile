FROM python:3.13-slim

WORKDIR /app

# Копируем uv из официального образа
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Настройки uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Устанавливаем зависимости (без исходников проекта — для кэширования слоя)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Копируем исходники
COPY src/ ./src/

# Добавляем src в PYTHONPATH
ENV PYTHONPATH=/app/src

# Активируем venv
ENV PATH="/app/.venv/bin:$PATH"

