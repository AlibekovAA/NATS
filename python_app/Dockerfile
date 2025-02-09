FROM python:3.12-slim AS base

WORKDIR /app

LABEL maintainer="aslan.alibekov.2017@mail.ru"
LABEL version="0.1.0"
LABEL description="Python FastAPI NATS Application"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

FROM base AS production

COPY app app/
COPY mypy.ini .

RUN mypy app/

ENV PYTHONPATH=/app
ENV TZ=Europe/Moscow

HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
