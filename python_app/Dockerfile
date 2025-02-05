FROM python:3.12-slim AS base

WORKDIR /app

LABEL maintainer="aslan.alibekov.2017@mail.ru"
LABEL version="0.1.0"
LABEL description="Python FastAPI NATS Application"

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

FROM base AS production

COPY . .

RUN mypy app/

ENV PYTHONPATH=/app
ENV TZ=Europe/Moscow

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
