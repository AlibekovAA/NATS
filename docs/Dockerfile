FROM python:3.12-slim

WORKDIR /docs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["mkdocs", "serve", "-a", "0.0.0.0:8001"]
