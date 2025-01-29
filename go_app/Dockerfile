FROM golang:1.21 AS builder

WORKDIR /app

LABEL maintainer="aslan.alibekov.2017@mail.ru"
LABEL version="0.1.0"
LABEL description="Go NATS Client Application"

RUN apt-get update && apt-get install -y libpcap-dev

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=1 GOOS=linux go build -o main .

FROM debian:stable-slim

WORKDIR /app

LABEL maintainer="aslan.alibekov.2017@mail.ru"
LABEL version="0.1.0"
LABEL description="Go NATS Client Application"

RUN apt-get update && apt-get install -y libpcap0.8 tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/main .

ENV TZ=Europe/Moscow

ENTRYPOINT ["/app/main"]
