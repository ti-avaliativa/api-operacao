FROM python:3.9-slim

WORKDIR /code

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app
COPY ./gunicorn_config.py /code/app
COPY ./.env.production /code/.env

ENV PYTHONPATH="/code:${PYTHONPATH}"

# Variáveis de ambiente (serão sobrescritas pelo .env em produção)
ENV API_KEY=sk-avaliarede-7K9mP2xR8vN4qW6tE3yU1sA5oI9jL7fG2hD6kM8nB4vC3xZ1qW5eR9tY8uI7oP6aS4dF3gH2jK9mN8bV5cX4zQ1wE6rT3yU8iO7pL5kJ9hG4fD2sA1qW3eR6tY9uI8oP7aS5dF4gH3jK2mN1
ENV DB_HOST=av-rede.ctrnya9tildy.us-west-2.rds.amazonaws.com
ENV DB_PORT=3306
ENV DB_USER=avaliaredeApiOperacao
ENV DB_PASSWORD=Ti@valiativa$%2025

# OTIMIZAÇÕES PARA EVITAR 503
ENV WORKERS=4
ENV PYTHONUNBUFFERED=1

WORKDIR /code/app

# NOTA: Usando app.api_operacao:app (arquivo principal da API)
CMD ["gunicorn", "--config", "gunicorn_config.py", "app.api_operacao:app"]