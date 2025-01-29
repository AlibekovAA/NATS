FROM python:3.12-slim

WORKDIR /app

LABEL maintainer="aslan.alibekov.2017@mail.ru"
LABEL version="0.1.0"
LABEL description="Python FastAPI NATS Application"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mypy app/

ENV PYTHONPATH=/app
ENV TZ=Europe/Moscow

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
